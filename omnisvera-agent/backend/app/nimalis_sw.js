/*
 * Nimalis runtime cache.
 *
 * The backend replaces the version marker using the current PCK signature.
 * The old cache is then removed and only the changed runtime files are fetched
 * again.  The first release is still one large PCK; splitting
 * that PCK into city/forest/content packs is the next optimization.
 */
const CACHE_VERSION = "nimalis-runtime-vCURRENT";
const CACHE_NAME = CACHE_VERSION;

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys
        .filter((key) => key.startsWith("nimalis-runtime-") && key !== CACHE_NAME)
        .map((key) => caches.delete(key)),
    )).then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || !url.pathname.startsWith("/nimalis/")) {
    return;
  }

  // HTML and this worker are the update check.  They must reach the server.
  if (url.pathname.endsWith("/nimalis.html") || url.pathname.endsWith("/sw.js") || url.pathname.endsWith("/release.json")) {
    event.respondWith(fetch(request, { cache: "no-store" }));
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (!response || (!response.ok && response.type !== "opaque")) return response;
        const copy = response.clone();
        event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.put(request, copy)));
        return response;
      });
    }),
  );
});
