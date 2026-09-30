/* Bámi-Sọ̀rọ̀ service worker — app-shell precache + runtime caching. */
const PRECACHE = "bami-soro-shell-v2";
const RUNTIME = "bami-soro-runtime-v2";
const PRECACHE_URLS = [
  "/",
  "/auth",
  "/dashboard",
  "/dashboard/translate",
  "/dashboard/history",
  "/hero-voiceover.jpg",
  "/manifest.webmanifest",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/icon-apple-touch.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(PRECACHE)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => ![PRECACHE, RUNTIME].includes(k)).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // Never intercept API calls (cross-origin backend): they need live auth/data.
  if (url.origin !== self.location.origin) return;

  // Navigations: network-first with offline fallback to cached shell.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(PRECACHE).then((cache) => cache.put("/", copy));
          return response;
        })
        .catch(() =>
          caches
            .match("/")
            .then((cached) => cached || caches.match(request))
            .then((fallback) => fallback || new Response("Offline", { status: 503 }))
        )
    );
    return;
  }

  // Same-origin assets: stale-while-revalidate.
  event.respondWith(
    caches.match(request).then((cached) => {
      const fresh = fetch(request)
        .then((response) => {
          if (response && response.ok) {
            const copy = response.clone();
            caches.open(RUNTIME).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => cached);
      return cached || fresh;
    })
  );
});