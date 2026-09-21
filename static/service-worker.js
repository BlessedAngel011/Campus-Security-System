const CACHE_NAME = "ufh-campus-security-v2";

const STATIC_ASSETS = [
    "/",
    "/login",
    "/static/style.css",
    "/static/ufh-logo.png",
    "/static/alice-campus.png",
    "/static/icon-192.png",
    "/static/icon-512.png",
    "/static/manifest.json"
];


/* =========================================================
   INSTALL
========================================================= */

self.addEventListener("install", event => {

    event.waitUntil(

        caches
            .open(CACHE_NAME)
            .then(cache => {

                console.log("UFH Security: caching app assets");

                return cache.addAll(STATIC_ASSETS);

            })

    );

    self.skipWaiting();

});


/* =========================================================
   ACTIVATE
   Remove old cache versions
========================================================= */

self.addEventListener("activate", event => {

    event.waitUntil(

        caches
            .keys()
            .then(cacheNames => {

                return Promise.all(

                    cacheNames.map(cacheName => {

                        if (cacheName !== CACHE_NAME) {

                            console.log(
                                "UFH Security: deleting old cache",
                                cacheName
                            );

                            return caches.delete(cacheName);

                        }

                    })

                );

            })

    );

    self.clients.claim();

});


/* =========================================================
   FETCH
========================================================= */

self.addEventListener("fetch", event => {

    const request = event.request;


    /* Only handle GET requests */

    if (request.method !== "GET") {
        return;
    }


    const requestURL = new URL(request.url);


    /* Only handle requests from this application */

    if (requestURL.origin !== self.location.origin) {
        return;
    }


    /*
       HTML/navigation requests:
       Try network first.

       This is important for dashboards because students,
       security officers and administrators must receive
       current information from Flask and SQLite.
    */

    if (request.mode === "navigate") {

        event.respondWith(

            fetch(request)

                .then(response => {

                    return response;

                })

                .catch(() => {

                    return caches.match(request)
                        .then(cachedResponse => {

                            if (cachedResponse) {
                                return cachedResponse;
                            }

                            return caches.match("/");

                        });

                })

        );

        return;

    }


    /*
       Static assets:
       Cache first, then network.
    */

    if (requestURL.pathname.startsWith("/static/")) {

        event.respondWith(

            caches
                .match(request)
                .then(cachedResponse => {

                    if (cachedResponse) {
                        return cachedResponse;
                    }


                    return fetch(request)
                        .then(networkResponse => {

                            if (
                                !networkResponse ||
                                networkResponse.status !== 200
                            ) {

                                return networkResponse;

                            }


                            const responseClone =
                                networkResponse.clone();


                            caches
                                .open(CACHE_NAME)
                                .then(cache => {

                                    cache.put(
                                        request,
                                        responseClone
                                    );

                                });


                            return networkResponse;

                        });

                })

        );

    }

});