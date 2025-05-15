const http = require('http');

// This will store the latest coords posted from the browser
let currentCoords = { lon: null, lat: null };

const requestListener = (req, res) => {

    // set this host:port using config
    res.setHeader('Access-Control-Allow-Origin', 'localhost:5005');

    if (req.method === 'GET') {
        // Serve current GPS
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify(currentCoords));
    } else if (req.method === 'POST') {
        // Accept new coordinates from browser
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                // console.log("body: " + body);
                if (data.lon !== undefined && data.lat !== undefined) {
                    currentCoords = { lon: data.lon, lat: data.lat };
                    res.end(JSON.stringify({ status: 'ok' }));
                } else {
                    res.statusCode = 400;
                    res.end(JSON.stringify({ status: 'error', message: 'Invalid data' }));
                }
            } catch (err) {
                res.statusCode = 500;
                res.end(JSON.stringify({ status: 'error', message: err.message }));
            }
        });
    } else {
        res.statusCode = 405;
        res.end('Method Not Allowed');
    }
};

const server = http.createServer(requestListener);

const config = require('../../config/map.json');
const server_host = config.MAP.find(item => item.GPS_HOST)['GPS_HOST'];
const server_port = config.MAP.find(item => item.GPS_PORT)['GPS_PORT'];

server.listen(server_port, server_host , () => {
    console.log("JS GPS is listening on " + server_host + ":" + server_port);
});
