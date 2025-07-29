// [START initialize_firebase_in_sw]
importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js');

// TODO: Replace with your Firebase project config
firebase.initializeApp({
  apiKey: "AIzaSyCHHIovN0SCj7DTuCni2NY1IsCSIRRgFnE",
  authDomain: "pwapush-4e4e4.firebaseapp.com",
  projectId: "pwapush-4e4e4",
  storageBucket: "pwapush-4e4e4.firebasestorage.app",
  messagingSenderId: "876451632085",
  appId: "1:876451632085:web:bf98d777d19e45bb00e35c",
  measurementId: "G-P6EVG2YPTR"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-192x192.png',
    tag: 'onebee-notification', // Prevents duplicate notifications
    requireInteraction: false,
    silent: false
  };
  self.registration.showNotification(notificationTitle, notificationOptions);
});
// [END initialize_firebase_in_sw] 