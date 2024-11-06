// import Geolocation from 'ol/Geolocation.js';
//
// const geolocation = new Geolocation({
//     trackingOptions: {
//         enableHighAccuracy: false,
//     },
// });
//
// geolocation.setTracking(true)
//
// geolocation.on('error', function (error) {
//     const info = document.getElementById('info');
//     return error;
// });
//
// function update(){
//     if (geolocation.getTracking() == true) {
// //         return geolocation.getPosition();
//     }
// }
//
// geolocation.on('change', function () {
//     update();
// });


// const http = require('node:http');

// const server = http.createServer({ keepAliveTimeout: 60000 }, (req, res) => {
//   res.writeHead(200, { 'Content-Type': 'application/json' });
//   res.end(JSON.stringify({
//     data: update(),
//   }));
// });
//
// server.listen(5400);
//// Close the server after 10 seconds
//setTimeout(() => {
//  server.close(() => {
//    console.log('server on port 8000 closed successfully');
//  });
//}, 10000);
//
