self.addEventListener('install', function(event) {
  self.skipWaiting();
});
self.addEventListener('activate', function(event) {
  self.clients.claim();
});
self.addEventListener('push', function(event) {
  event.waitUntil(
    self.registration.showNotification('Test Push', {
      body: 'This is a test push notification!',
      icon: '/static/icons/icon-192x192.png'
    })
  );
}); 