/* NZ Economic Watch — service worker.
   Makes the dashboard installable and usable offline.

   Strategy (revised so updates always show):
   - The page + data (index.html, "./", market-data.js): NETWORK-FIRST — always
     try the latest from the server, fall back to cache only when offline. This
     is what fixes "I still see the old version after a deploy".
   - Static assets (icons, manifest): cache-first, refreshed in the background.
   Bump CACHE on any shell change so old caches are cleared on activate. */
const CACHE = "nz-econ-watch-v2";
const SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon-192.png",
  "./icon-512.png",
  "./apple-touch-icon.png"
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function networkFirst(req) {
  return fetch(req)
    .then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(req, copy));
      return res;
    })
    .catch(() => caches.match(req).then((hit) => hit || caches.match("./index.html")));
}

function cacheFirst(req) {
  return caches.match(req).then((hit) =>
    hit || fetch(req).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(req, copy));
      return res;
    })
  );
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  const isDoc = req.mode === "navigate" || url.pathname.endsWith("/") || url.pathname.endsWith("index.html");
  const isData = url.pathname.endsWith("market-data.js");
  if (isDoc || isData) {
    e.respondWith(networkFirst(req));   // always prefer fresh
  } else {
    e.respondWith(cacheFirst(req));     // icons, manifest
  }
});
