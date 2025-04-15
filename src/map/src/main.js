import Feature from 'ol/Feature.js';
import Geolocation from 'ol/Geolocation.js';
import Map from 'ol/Map.js';
import Point from 'ol/geom/Point.js';
import Circle from 'ol/geom/Circle.js';
import View from 'ol/View.js';
import {toRadians} from 'ol/math.js';
import {DragRotateAndZoom, defaults as defaultInteractions} from 'ol/interaction.js';
import {OverviewMap, Control, defaults as defaultControls} from 'ol/control.js';
import {Circle as CircleStyle, Fill, Stroke, Style} from 'ol/style.js';
import {OSM, Vector} from 'ol/source.js';
import VectorSource from 'ol/source/Vector.js';
import {Tile as TileLayer, Vector as VectorLayer} from 'ol/layer.js';
import {toStringHDMS, toStringXY, degreesToStringHDMS} from 'ol/coordinate.js';
import {transform as xform, fromLonLat, toLonLat} from 'ol/proj.js';
import {Heatmap as HeatmapLayer} from 'ol/layer.js';


/*
docs @ https://openlayers.org/en/latest/apidoc/
*/

const enable_hardware = false;
var fix;
var click = 0;
var features = [];
var coordinate;
const tracking_ind = document.getElementById('tracking_ind');
const output = document.getElementById('output');

class RotateNorthControl extends Control {

    constructor(opt_options) {
        const options = opt_options || {};
        const n_button = document.createElement('button');
        n_button.innerHTML = 'N';

        const n_element = document.createElement('div');
        n_element.className = 'rotate-north ol-unselectable ol-control';
        n_element.id = 'rotate-north';
        n_element.appendChild(n_button);

        super({
            element: n_element,
            target: options.target,
        });

        n_button.addEventListener('click', this.handleRotateNorth.bind(this), false);
    }

    handleRotateNorth() {
        this.getMap().getView().setRotation(0);
    }
}

function handleTrackingButton() {

    tracking_ind.innerHTML = "<div id='tracking_ind' class='ol-unselectable' style='' width='6' height='22'>&nbsp;</div>";

    if (enable_hardware){
        if (fix == true) {
            tracking_ind.style='background:purple'; // online w/fix
        } else {
            tracking_ind.style='background:orange'; // offline
        }
    } else {
        if (geolocation){

            geolocation.setTracking = !geolocation.getTracking();
            if (geolocation.getTracking() == false){
                tracking_ind.style='background:yellow'; // warning
            } else {
                tracking_ind.style='background:red';    // offline
            }

            const coordJS = geolocation.getPosition();
            if (coordJS) {
                positionFeature.setGeometry(new Point(coordJS));
                view.setCenter(coordJS);
                output.innerHTML = '';
                tracking_ind.style='background:green';  // online
            }

        } else {
            tracking_ind.style='background:red';
        }
    }
}

class TrackingControl extends Control {
    constructor(opt_options) {

        const options = opt_options || {};

        const t_button = document.createElement('button');
        t_button.innerHTML = 'T';

        const t_element = document.createElement('div');
        t_element.className = 'track ol-unselectable ol-control';
        t_element.id = 'track';
        t_element.appendChild(t_button);

        super({
            element: t_element,
            target: options.target,
        });

        const t_button_hi = document.getElementById('track');
        t_button.addEventListener('click', handleTrackingButton.bind(this), false);
    }
}

function setHeaders(xhttp, host){
    xhttp.setRequestHeader('Access-Control-Allow-Origin', host);
    xhttp.setRequestHeader('Access-Control-Allow-Methods', 'GET');
    xhttp.setRequestHeader('Content-Type', 'text/html');
    xhttp.setRequestHeader('Access-Control-Allow-Headers', 'Content-Type, Access-Control-*');
};

const positionFeature = new Feature();
const accuracyFeature = new Feature();
const currentWebMercator = fromLonLat([-105.068617, 39.916905]);

positionFeature.setStyle(
    new Style({
            image: new CircleStyle({
                radius: 5,
            fill: new Fill({
                color: '#0000FF',
            }),
            stroke: new Stroke({
                color: '#FFF',
                width: 1,
            }),
        }),
    })
);

const view = new View({
    center: currentWebMercator,
    /*
        #IDEA 'Zoom 5000': A single button that magnifies the current view to a radius of n ft.
    */
    zoom: 19,
});

const geolocation = new Geolocation({
    // enableHighAccuracy must be set to true to have the heading value.
    trackingOptions: {
        enableHighAccuracy: true,
    },
    projection: view.getProjection(),
});

geolocation.setTracking(true);


function getLocation(){
    var xhttp = new XMLHttpRequest();
    var block = true;
    xhttp.open("GET", 'http://gps.localhost:5004/position', block);  // #ToDO: find a way to not hardcode URL
    setHeaders(xhttp, 'gps.localhost:5004');

    xhttp.onload = function(){
        const resp = xhttp.response;
        let json = JSON.parse(resp);
        var hdweCoords = [json['lon'], json['lat']]
        coordinate = hdweCoords;
    };
    xhttp.send();
}

if (enable_hardware) {
    coordinate = currentWebMercator;
    setInterval(function() {
        getLocation();
        animate(coordinate);
        update(coordinate);
        console.log('enable_hardware: ' + coordinate);
    }, 1000);
};

geolocation.on('change', function () {

    const coordJS = geolocation.getPosition();
    const jsCoords = toLonLat(coordJS);
    const payload = {
        lon: jsCoords[0],
        lat: jsCoords[1]
    };

    // Send coords to Node server
    fetch('http://localhost:3000', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    // console.log("hi " + payload['lon'] + ", " + payload['lat']);
});

geolocation.on('error', function (error) {
    if  (!enable_hardware) {
        output.innerHTML = error.message;
        output.style.display = '';
    }
    handleTrackingButton();
});

function el(id) {
    return document.getElementById(id);
}

const overviewMapControl = new OverviewMap({
    // see in overviewmap-custom.html to see the custom CSS used
    className: 'ol-overviewmap ol-custom-overviewmap',
    layers: [
        new TileLayer({
        source: new OSM(
                    new Vector({
                         features : [accuracyFeature]
                    }),
            ),
        }),
    ],
    collapseLabel: '\u00BB',
    label: '\u00AB',
    collapsed: true,
    rotateWithView: true,
});

const blur = document.getElementById('blur');
const radius = document.getElementById('radius');

const heatMap = new HeatmapLayer({
    source: new Vector({features:features}),
    blur: parseInt(blur.value, 10),
    radius: parseInt(radius.value, 10),
    weight: .5
});

blur.addEventListener('input', function () {
  heatMap.setBlur(parseInt(blur.value, 10));
});

radius.addEventListener('input', function () {
  heatMap.setRadius(parseInt(radius.value, 10));
});

const info = document.getElementById('info');

let currentFeature;

const displayFeatureInfo = function (pixel, target) {
  const feature = target.closest('.ol-control')
    ? undefined
    : map.forEachFeatureAtPixel(pixel, function (feature) {
        return feature;
      });
  if (feature) {
    info.style.left = pixel[0] - 80 + 'px';
    info.style.top = pixel[1] - 80 + 'px';
    if (feature !== currentFeature) {
      info.style.visibility = 'visible';
      info.innerText = feature.get('LINE0'.toUpperCase()) + feature.get('LINE1') + feature.get('LINE2');
    }
  } else {
    info.style.visibility = 'hidden';
  }
  currentFeature = feature;
};

function getPointStyle(signal_color) {
    // ANY signal: origin point
    var pointstyle = new Style({
          stroke: new Stroke({
              color: 'rgba(0,0,0,1.0)',
              width: 1
          }),
          fill: new Fill({
              color: signal_color
          })
    });
    return pointstyle;
}


function getCircleStyle(signal_color, strength) {
    // Wifi Signals
    var circlestyle = new Style({
          stroke: new Stroke({
              color: signal_color,
              width: 1
          }),
          fill: new Fill({
              color: signal_color
          })
    });

    return circlestyle;
}

function getAltCircleStyle(signal_color, strength) {
    // ? signals
    var circlestyle = new Style({
          stroke: new Stroke({
              color: signal_color,
              width: (strength + 100)/10*10 // stroke width is strength
          })
    });

    return circlestyle;
}

function getConcentricStyle(signal_color) {
    // TRX signals
    var circlestyle = new Style({
          stroke: new Stroke({
              color: signal_color,
              width: 2
          }),
    });

    return circlestyle;
}

function addCircle(source, coordinate, signal_color, strength, cell) {

    const circleFeature = new Feature({
      geometry: new Circle(coordinate, (strength + 100)/10*10),
    });

    circleFeature.setStyle(getCircleStyle(signal_color, strength));

    circleFeature.set('LINE0', cell.SSID  + '\n', true);
    circleFeature.set('LINE1', cell.BSSID  + '\n', true);
    circleFeature.set('LINE2', "[" + parseInt(strength) + "]", true);

    source.addFeature(circleFeature);
    return circleFeature;
}

function addPoint(source, id, lonlat, signal_color, strength, cell) {

    const pointFeature = new Feature({
      geometry: new Circle(fromLonLat(lonlat), 1),
    });

    pointFeature.setStyle(getPointStyle(signal_color));
    pointFeature.setId(id);
    pointFeature.set('LINE0', cell.SSID + '\n', true);
    pointFeature.set('LINE1', lonlat[0] + ", " + lonlat[1] + '\n', true);
    pointFeature.set('LINE2', "[" + parseInt(strength) + "]", true);

    source.addFeature(pointFeature);

}

function createConcentric(source, coordinate, circles, signal_color, strength, cell) {

    for (var total = 0; total < circles; total = total+1) {
        // var diameter = (circles-total) * (strength + 100)/10*10;

        const concentricFeature = new Feature({
          geometry: new Circle(coordinate, (circles-total) * (strength + 100)/10*10),
        });

        concentricFeature.setStyle(getConcentricStyle(signal_color));

        concentricFeature.set('LINE0', cell.text_attributes['ALPHATAG']  + '\n', true);
        concentricFeature.set('LINE1', cell.text_attributes['FREQ1'] != null? cell.text_attributes['FREQ1'] + 'Mhz\n':cell.text_attributes['FREQ2'] + 'Mhz\n', true);
        concentricFeature.set('LINE2', cell.text_attributes['SITE'], true);

        source.addFeature(concentricFeature);
    }
}

function createCircle(source, coordinate, signal_color, strength, cell) {
    addCircle(source, coordinate, signal_color, strength, cell);
}

function createPoint(source, id, coordinate, signal_color, strength, cell) {
    addPoint(source, id, coordinate, signal_color, strength, cell);
}

const map = new Map({
    controls: defaultControls().extend([
        overviewMapControl,
        new RotateNorthControl(),
        new TrackingControl()
    ]),
    interactions: defaultInteractions().extend([new DragRotateAndZoom()]),
    layers: [
        new TileLayer({
            source: new OSM(),
        }),
        new VectorLayer({
            source: new Vector({features:features}),
        }),
        // vectorlayers per source; updates need to be atomic.
//        new VectorLayer({
//            source: heatMap,
//        }),
    ],
    target: 'map',
    view: view,
});

const v_layer = (
    map.getAllLayers()
        .find(function (layer) {
            if (layer instanceof VectorLayer
                    && layer.getSource() instanceof Vector
                )
            {
                return layer;
            }
        })
);

map.on('pointermove', function (evt) {
    if (evt.dragging) {
        info.style.visibility = 'hidden';
        currentFeature = undefined;
        return;
    }

    const pixel = map.getEventPixel(evt.originalEvent);
    displayFeatureInfo(pixel, evt.originalEvent.target);
});

map.on('click', function (mapClickEvent) {
    displayFeatureInfo(mapClickEvent.pixel, mapClickEvent.originalEvent.target);
})

map.getTargetElement().addEventListener('pointerleave', function () {
    currentFeature = undefined;
    info.style.visibility = 'hidden';
});

/*
#TODO: support
overlaid data,
satellite images & wavelengths,
different resolutions
*/

new VectorLayer({
    map: map,
    source: new Vector({
        features: [accuracyFeature, positionFeature],
    }),
});

new VectorLayer({
    map: overviewMapControl,
    source: new Vector({
        features: [accuracyFeature],
    }),
});

function animate(coordinate) {

    console.log('animate coordinate: ' + coordinate);

    function colorUniqId(data, splt){
           var parts = data.split(splt);
           var R = (parseInt(parts[0], 16) + parseInt(parts[1], 16)) % 255;
           var G = (parseInt(parts[2], 16) + parseInt(parts[3], 16)) % 255;
           var B = (parseInt(parts[4], 16) + parseInt(parts[5], 16)) % 255;
           return [R,G,B];
    };

    const hdweCoords = fromLonLat(coordinate);

    var xhttp = new XMLHttpRequest();
    let URL = "http://map.localhost:5005/data";  // #ToDO: find a way to not hardcode URL
    xhttp.open("GET", URL, true);

    setHeaders(xhttp, 'map.localhost:5005');

    xhttp.onload = function(){
        const resp = xhttp.response;

        if (xhttp.status == 200){

            var _signals = JSON.parse(resp);

            var source = v_layer.getSource();
            source.clear();

            if (_signals.wifi > null) {
                _signals.wifi.forEach(function(cell) {

                    if (!cell.is_mute && cell.tracked){

                        for (const sgnl of cell.signal_cache) {

                            var _color = colorUniqId(cell.BSSID, ':');
                            var lonlat = fromLonLat([sgnl.lon, sgnl.lat]);
                            var sgnlPt = [sgnl.lon, sgnl.lat];
                            var sgnlStrength = parseInt(sgnl.sgnl);

                            var c_signal_color = 'rgba(' + _color + ',' + parseFloat( ((sgnlStrength + 100)/100).toFixed(2) ) + ')';
                            var p_signal_color = 'rgba(' + _color + ', 1.0)';

                            //console.log("SIGNALPOINT: [" + sgnl.id + "] " + cell.BSSID + " c_signal_color:" + c_signal_color + " sgnl.lon:" + sgnl.lon + " sgnl.lat:" +  sgnl.lat + " sgnl.sgnl:" +  sgnlStrength );

                            // choose the feature based on signal type and
                            // pass one call
                            // SignalPoint(source, id, point, p_signal_color, style, c_signal_color, strength, cell)

                            createPoint(source, sgnl.id, sgnlPt, p_signal_color, sgnlStrength, cell);
                            createCircle(source, lonlat, c_signal_color, sgnlStrength, cell);

                       }
                    }
                });
            };

            if (_signals.trx > null) {
                _signals.trx.forEach(function(cell) {
                    if (!cell.is_mute && cell.tracked) {

                        //  special processing to make string of hex look like a BSSID
                        var uniqId = cell.id.replace('-','').substring(0,12).match(/.{1,2}/g).join(':');

                        var _color = colorUniqId(uniqId, ':');
                        var lonlat = fromLonLat([cell.lon, cell.lat]);
                        var sgnlStrength = -77; // WHERE FROM?!
                        var numConcentrics = 10;

                        var p_signal_color = 'rgba(' + _color + ', 1.0)';

                        // symbology for TRX SignalPoints
                        createConcentric(source, lonlat, numConcentrics, p_signal_color, sgnlStrength, cell);
                    }
                });
            }
            /*
            if (_signals.sdr) {
                _signals.sdr.forEach(function(cell) {
                    if (!cell.is_mute && cell.tracked) {
                        console.log('SDR: ' +  cell);
                        // symbology for SDR SignalPoints
                        // createConcentric(source, lonlat, 10, p_signal_color, sgnlStrength, cell);
                    }
                });
            }

            if (_signals.cam) {
                _signals.cam.forEach(function(cell) {
                    if (!cell.is_mute && cell.tracked) {
                        console.log('CAM: ' +  cell);
                        // origin points
                        // createPoint(source, sgnl.id, sgnlPt, p_signal_color, sgnlStrength, cell);
                    }
                });
            }

            if (_signals.arx) {
                _signals.arx.forEach(function(cell) {
                    if (!cell.is_mute && cell.tracked) {
                        console.log('ARX: ' +  cell);
                        // (NEW SYMBOL; moving or static)
                        // createPoint(source, sgnl.id, sgnlPt, p_signal_color, sgnlStrength, cell);
                    }
                });
            }

            if (_signals.net) {
                _signals.net.forEach(function(cell) {
                    if (!cell.is_mute && cell.tracked) {
                        console.log('NET: ' +  cell);
                        // (NEW SYMBOL for networked instances; moving or static)
                        // createPoint(source, sgnl.id, sgnlPt, p_signal_color, sgnlStrength, cell);
                    }
                });
            }
            */

            map.render();
            return true;
        } else {
            return false;
        };
    };
    xhttp.send();
};

function update(coordinate) {

    console.log('update coordinate: ' + coordinate);
    var source = v_layer.getSource();

    var coordinatesList = document.getElementById("coordinatesList");
    coordinatesList.innerHTML = "coordinate: " + coordinate;

    var featuresList = document.getElementById("featuresList");
    featuresList.innerHTML = "Features: " + source.getFeatures().length;

    positionFeature.setGeometry(new Point(fromLonLat(coordinate)));

    positionFeature.set('LINE0', 'ORIGIN'  + '\n', true);
    positionFeature.set('LINE1', coordinate[0] + ", " + coordinate[1]   + '\n', true);
    positionFeature.set('LINE2', '', true);

    view.setCenter(fromLonLat(coordinate));
    handleTrackingButton();
};
