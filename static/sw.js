const CACHE = "acaciafund-v1";
const ASSETS = ["/", "/offline/"];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    fetch(e.request)
      .then((r) => (caches.open(CACHE).then((c) => c.put(e.request, r.clone())), r))
      .catch(() => caches.match(e.request).then((r) => r || caches.match("/offline/")))
  );
});
