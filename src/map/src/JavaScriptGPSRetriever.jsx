import Geolocation from 'ol/Geolocation.js';

const geolocation = new Geolocation({
    trackingOptions: {
        enableHighAccuracy: false,
    },
});

geolocation.setTracking(true)

geolocation.on('error', function (error) {
    console.log('error!');
    return error;
});

function update(){
    if (geolocation.getTracking() == true) {
        console.log('update...');
        return geolocation.getPosition();
    }
}

geolocation.on('change', function () {
    console.log('geolocation change...');
    update();
});


const http = require('node:http');

const server = http.createServer({ keepAliveTimeout: 60000 }, (req, res) => {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({
    console.log('server on port 5400 called update()');
    data: update(),
  }));
});

server.listen(5183);
// Close the server after 10 seconds
setTimeout(() => {
 server.close(() => {
   console.log('server on port 5400 closed successfully');
 });
}, 10000);

