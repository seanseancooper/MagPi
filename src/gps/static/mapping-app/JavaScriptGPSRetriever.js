import Geolocation from 'ol/Geolocation.js';

const geolocation = new Geolocation({
    trackingOptions: {
        enableHighAccuracy: false,
    },
});

geolocation.setTracking(true)

geolocation.on('error', function (error) {
    const info = document.getElementById('info');
    return error;
});

function update(){
    if (geolocation.getTracking() == true) {
        return geolocation.getPosition();
    }
}

geolocation.on('change', function () {
    update();
});

update();