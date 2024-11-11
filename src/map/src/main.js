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
import {transform as xform, fromLonLat} from 'ol/proj.js';
import {Heatmap as HeatmapLayer} from 'ol/layer.js';
//import {JSONFeature as JSONFeature} from 'ol/format/JSONFeature.js'; <-- abstract, doesn't import. read direct from response

var click = 0;
var tmpCoord;
var features = [];
var selMarker;

/*
docs @ https://openlayers.org/en/latest/apidoc/
*/

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

class TrackingControl extends Control {
    /* REQUIRES JAVASCRIPT AND GEOLOCATION */
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
        t_button.addEventListener('click', this.handleTrackingButton.bind(this), false);
    }

    handleTrackingButton() {

        if (geolocation){
            geolocation.setTracking(!geolocation.getTracking());
        }

        if (geolocation.getTracking() == true){
            info.innerHTML = "<div id=\"tracking_ind\" class=\"ol-unselectable\" style=\"background:green\" width=\"6\" height=\"22\">&nbsp;</div>";
            info.style.display = '';
            const coordJS = geolocation.getPosition();
            positionFeature.setGeometry(new Point(coordJS));
            view.setCenter(coordJS);
        } else {
            info.innerHTML = "<div id=\"tracking_ind\" class=\"ol-unselectable\" style=\"background:red\" width=\"6\" height=\"22\">&nbsp;</div>";
            info.style.display = '';
        }
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

// a default value to get us started.
const currentWebMercator = fromLonLat([-105.0437, 39.9168]);

const view = new View({
    center: currentWebMercator,
    /*
        #IDEA 'Zoom 5000': A single button that magnifies the current view to a radius of n ft.
    */
    zoom: 19,
});

const geolocation = new Geolocation({
    trackingOptions: {
        enableHighAccuracy: true,
    }
});

geolocation.setTracking(true);

geolocation.on('change', function (evt) {

    var xhttp = new XMLHttpRequest();
    var block = true;
    xhttp.open("GET", 'http://gps.localhost:5004/position', block);

    setHeaders(xhttp, 'gps.localhost:5004');

    xhttp.onload = function(){
        const resp = xhttp.response;
        let json = JSON.parse(resp);
        var hdweCoords = [json['GPS']['lon'], json['GPS']['lat']]
        animate(hdweCoords);
        update(hdweCoords);
    };

    xhttp.send();

});

geolocation.on('error', function (error) {
    const info = document.getElementById('info');
    info.innerHTML = error.message;
    info.style.display = '';
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

        concentricFeature.set('LINE0', cell.SSID  + '\n', true);
        concentricFeature.set('LINE1', cell.BSSID  + '\n', true);
        concentricFeature.set('LINE2', "[" + parseInt(strength) + "]", true);

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

    const hdweCoords = fromLonLat(coordinate);

    var xhttp = new XMLHttpRequest();
    let URL = "http://wifi.localhost:5006/tracked";
    xhttp.open("GET", URL, true);

    setHeaders(xhttp, 'wifi.localhost:5006');

    xhttp.onload = function(){
        const resp = xhttp.response;

        if (xhttp.status == 200){

            var tracked_signals = JSON.parse(resp);

            var source = v_layer.getSource();
            source.clear();

            tracked_signals.forEach(function(cell) {

                if (!cell.is_mute){

                    let _color = (function(){
                           var parts = cell.BSSID.split(':');
                           var R = (parseInt(parts[0], 16) + parseInt(parts[1], 16)) % 255;
                           var G = (parseInt(parts[2], 16) + parseInt(parts[3], 16)) % 255;
                           var B = (parseInt(parts[4], 16) + parseInt(parts[5], 16)) % 255;
                           return [R,G,B];
                    })(cell);

                    for (const s of cell.signal_cache) {

                        const sgnl = JSON.parse(s);
                        var lonlat = fromLonLat([sgnl.lon, sgnl.lat]);
                        var sgnlPt = [sgnl.lon, sgnl.lat];
                        var sgnlStrength = parseInt(sgnl.sgnl);

                        var c_signal_color = 'rgba(' + _color + ',' + parseFloat( ((sgnlStrength + 100)/100).toFixed(2) ) + ')';
                        var p_signal_color = 'rgba(' + _color + ', 1.0)';

                        console.log("SIGNALPOINT: [" + sgnl.id + "] " + cell.BSSID + " c_signal_color:" + c_signal_color + " sgnl.lon:" + sgnl.lon + " sgnl.lat:" +  sgnl.lat + " sgnl.sgnl:" +  sgnlStrength );

                        // choose the feature based on signal type and
                        // pass one call SignalPoint(source, id, point, p_signal_color, style, c_signal_color, strength, cell)
                        createPoint(source, sgnl.id, sgnlPt, p_signal_color, sgnlStrength, cell);
                        createCircle(source, lonlat, c_signal_color, sgnlStrength, cell);
                        createConcentric(source, lonlat, 10, c_signal_color, sgnlStrength, cell);
                   }
                }
            });
            map.render();
            return true;
        } else {
            return false;
        };
    };
    xhttp.send();
};

function update(coordinate) {

    var source = v_layer.getSource();
    var featuresList = document.getElementById("featuresList");
    featuresList.innerHTML = "Features: " + source.getFeatures().length;

    positionFeature.setGeometry(new Point(fromLonLat(coordinate)));

    positionFeature.set('LINE0', 'ORIGIN'  + '\n', true);
    positionFeature.set('LINE1', coordinate[0] + ", " + coordinate[1]   + '\n', true);
    positionFeature.set('LINE2', '', true);

    view.setCenter(fromLonLat(coordinate));
};
