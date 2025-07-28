const CACHE_NAME = 'fastag-v1.0.0';
const STATIC_CACHE = 'fastag-static-v1.0.0';
const DYNAMIC_CACHE = 'fastag-dynamic-v1.0.0';

// Resources to cache immediately
const STATIC_RESOURCES = [
  '/',
  '/static/manifest.json',
  '/static/logo.png',
  '/static/customer.png',
  '/static/branding.jpg',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  '/api/',
  '/analytics/',
  '/locations',
  '/lanes',
  '/readers',
  '/kyc-users'
];

// Install event - cache static resources
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Caching static resources');
        return cache.addAll(STATIC_RESOURCES);
      })
      .then(() => {
        console.log('Static resources cached successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Error caching static resources:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Handle API requests
  if (isApiRequest(url.pathname)) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle static resources
  if (isStaticResource(url.pathname)) {
    event.respondWith(handleStaticRequest(request));
    return;
  }

  // Handle HTML pages
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(handleHtmlRequest(request));
    return;
  }
});

function isApiRequest(pathname) {
  return API_CACHE_PATTERNS.some(pattern => pathname.includes(pattern));
}

function isStaticResource(pathname) {
  return pathname.startsWith('/static/') || 
         pathname.includes('cdn.jsdelivr.net') || 
         pathname.includes('cdnjs.cloudflare.com');
}

async function handleApiRequest(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful API responses
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
  } catch (error) {
    console.log('Network failed for API request:', request.url);
  }

  // Fallback to cache
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  // Return offline page for API requests
  return new Response(
    JSON.stringify({ 
      error: 'No internet connection',
      message: 'Please check your connection and try again'
    }), 
    { 
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}

async function handleStaticRequest(request) {
  // Cache first for static resources
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('Failed to fetch static resource:', request.url);
    return new Response('Resource not available offline', { status: 404 });
  }
}

async function handleHtmlRequest(request) {
  try {
    // Try network first for HTML
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful HTML responses
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
  } catch (error) {
    console.log('Network failed for HTML request:', request.url);
  }

  // Fallback to cache
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  // Return offline page
  return caches.match('/offline.html');
}

// Background sync for offline actions
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  // Implement background sync logic here
  // For example, sync offline form submissions
  console.log('Performing background sync...');
}

// Push notifications (if needed in the future)
self.addEventListener('push', function(event) {
  const data = event.data.json();
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon,
      data: { url: data.url }
    })
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
}); 