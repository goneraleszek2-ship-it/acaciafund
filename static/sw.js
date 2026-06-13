const CACHE = "acaciafund-v2";
const ASSETS = [
  "/",
  "/index.html",
  "/learn/",
  "/learn.html",
  "/static/css/tailwind.min.css",
  "/static/css/custom.css",
  "/static/js/learning_hub.js",
  "/static/images/favicon.svg"
];

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
      .catch(() => caches.match(e.request).then((r) => r || caches.match("/")))
  );
});
