/**
 * directory.evemiss.com edge worker — Cloudflare Pages Advanced Mode entry
 * point (same pattern as evemiss.com's own worker: this file placed at the
 * build output root makes Pages run it as the request handler for every
 * request, giving the same env.ASSETS.fetch() binding a standalone Worker
 * would get).
 *
 * 1. Host canonicalization — serves directory.evemiss.com.
 * 2. Single-URL multilingual — one public URL per page. Language is
 *    negotiated per request: `lang` cookie (manual choice) > IP country >
 *    Accept-Language > English default. The localized tree (/zh/...) exists
 *    only as an internal build artifact; requests are rewritten to it here.
 *
 * Adding a language later: add its code to LANGS (+ country/accept rules),
 * build the tree under /<code>/ — no other worker change needed. Ported
 * from evemiss.com's worker/index.js pattern, trimmed to two languages.
 */
const CANONICAL_HOST = 'directory.evemiss.com';
const DEFAULT_LANG = 'en';
/** language codes with a built tree under /<code>/ */
const LANGS = ['zh'];
/** IP countries mapped to a non-default language */
const COUNTRY_LANG = {
  TW: 'zh',
  HK: 'zh',
  MO: 'zh',
};
/** Content-Language per lang code */
const CONTENT_LANG = {
  en: 'en',
  zh: 'zh-Hant',
};
const LANG_COOKIE = 'lang';
const COOKIE_ATTRS = 'Path=/; Max-Age=31536000; SameSite=Lax';

function cookieLang(request) {
  const cookie = request.headers.get('Cookie') || '';
  const m = cookie.match(/(?:^|;\s*)lang=([A-Za-z-]+)/);
  if (!m) return null;
  const v = m[1].toLowerCase();
  if (v === DEFAULT_LANG || LANGS.includes(v)) return v;
  return null;
}

function pickLang(request) {
  const fromCookie = cookieLang(request);
  if (fromCookie) return fromCookie;

  const country = request.cf && request.cf.country;
  if (country && COUNTRY_LANG[country]) return COUNTRY_LANG[country];

  const accept = (request.headers.get('Accept-Language') || '').toLowerCase();
  const first = accept.split(',')[0].trim().split(';')[0];
  if (first.startsWith('zh')) return 'zh'; // zh-tw / zh-hant / zh-hk / bare zh -> Traditional
  return DEFAULT_LANG;
}

/** true for HTML page routes; false for asset files (js/css/etc) */
function isPagePath(pathname) {
  const ext = pathname.match(/\.([a-z0-9]+)$/i);
  if (ext && ext[1].toLowerCase() !== 'html') return false;
  return true;
}

function withLangHeaders(res, lang) {
  const out = new Response(res.body, res);
  out.headers.append('Vary', 'Cookie');
  out.headers.set('Content-Language', CONTENT_LANG[lang] || lang);
  return out;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // --- host canonicalization ------------------------------------------
    if (url.hostname !== CANONICAL_HOST) {
      url.hostname = CANONICAL_HOST;
      url.protocol = 'https:';
      return Response.redirect(url.toString(), 301);
    }

    // --- language negotiation for page routes ----------------------------
    if ((request.method === 'GET' || request.method === 'HEAD') && isPagePath(url.pathname)) {
      const lang = pickLang(request);
      if (lang !== DEFAULT_LANG) {
        const localized = new URL(url);
        localized.pathname = `/${lang}${url.pathname === '/' ? '' : url.pathname}`;
        let res = await env.ASSETS.fetch(new Request(localized, request));
        if (res.status === 404) {
          // page not translated yet -- fall back to the default language
          res = await env.ASSETS.fetch(request);
          return withLangHeaders(res, DEFAULT_LANG);
        }
        return withLangHeaders(res, lang);
      }
      return withLangHeaders(await env.ASSETS.fetch(request), DEFAULT_LANG);
    }

    return env.ASSETS.fetch(request);
  },
};
