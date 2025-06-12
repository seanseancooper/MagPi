const socket = io();
const fft_size = 4096;
let center_freq = 100e6;                // Get this from sdr
const sampling_rate = 2.048e6;          // get this from config?? sdr??
const bgcolor = "#000099";

let latestBlockData = new Uint8Array(fft_size);             // Shared buffer to hold latest block data
let blockReady = false;
let latestPeakData = new Uint8Array(1024);                  // Hold latest peak data
let peakReady = false;
const signalMetadataMap = new Map();                        // key: highlight ID or position, value: metadata

const highlights = [
  { min_sel: 200, max_sel: 700, alpha: 0.3, color: "cyan" }
];

socket.on('connect', () => {
    console.log("Socket connected");
});

socket.on('block_data', (data) => {
    if (data) {                                             // 4096 complex numbers = 8192 float32 values
        const floatArray = new Float32Array(data);
        requestPeaks();                                     // trigger peaks for block
        latestBlockData = processBlockData(floatArray);     // convert to 0..255
        blockReady = true;
    } else {
        console.warn("Invalid block_data received");
    }
});

socket.on('peak_data', (peaks) => {
    if (peaks) {
        latestPeakData = peaks;
    }
});

socket.on('meta_data', (data) => {
    if (data) {
        signalMetadataMap = data;
    };
});

// Emit read_block
function requestBlock() {
    socket.emit('read_block');
}

function requestPeaks() {
    socket.emit('get_peaks');
}

function requestMetadata() {
    socket.emit('meta_data');
}

class DragManager {

  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.draggables = [];
    this.active = null;
    this.lastX = 0;

    canvas.addEventListener("mousedown", e => this._onMouseDown(e));
    window.addEventListener("mousemove", e => this._onMouseMove(e));
    window.addEventListener("mouseup", e => this._onMouseUp(e));
  }

  addDraggable({ hitTest, onDrag, onDragEnd = () => {} }) {
    this.draggables.push({ hitTest, onDrag, onDragEnd });
  }

  _onMouseDown(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    this.lastX = x;
    for (const d of this.draggables) {
      if (d.hitTest(x)) {
        this.active = d;
        break;
      }
    }
  }

  _onMouseMove(e) {
    if (!this.active) return;
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const dx = x - this.lastX;
    this.active.onDrag(dx);
    this.lastX = x;
  }

  _onMouseUp(e) {
    if (this.active) {
      this.active.onDragEnd();
      this.active = null;
    }
  }
}

class Highlight {

  constructor(min_sel, max_sel, alpha, color) {
    this._min_sel = min_sel;
    this._max_sel = max_sel;
    this.alpha = alpha;
    this.color = color;
  }

  get min_sel() {
    return this._min_sel;
  }

  set min_sel(value) {
    this._min_sel = value;
  }

  get max_sel() {
    return this._max_sel;
  }

  set max_sel(value) {
    this._max_sel = value;
  }

  draw(ctx, canvasHeight) {
    const width = this._max_sel - this._min_sel;
    ctx.globalAlpha = this.alpha;
    ctx.fillStyle = this.color.replace('ALPHA', this.alpha.toFixed(2));
    ctx.fillRect(this._min_sel, 0, width, canvasHeight);
    ctx.globalAlpha = 1.0; // reset
  }
}

class HighlightLayer {

  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext("2d");
    this.highlights = [];
  }

  addHighlight(min_sel, max_sel, alpha = 0.2, color = 'rgba(255,255,0,ALPHA)') {
    const hl = new Highlight(min_sel, max_sel, alpha, color);
    this.highlights.push(hl);
    this.render();
    return hl;
  }

  clearHighlights() {
    this.highlights = [];
    this.render();
  }

  render() {
    const { ctx, canvas } = this;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const hl of this.highlights) {
      hl.draw(ctx, canvas.height);
    }
  }
}

class DragManager {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.draggables = [];
    this.active = null;
    this.lastX = 0;

    canvas.addEventListener("mousedown", e => this._onMouseDown(e));
    window.addEventListener("mousemove", e => this._onMouseMove(e));
    window.addEventListener("mouseup", e => this._onMouseUp(e));
  }

  addDraggable({ hitTest, onDrag, onDragEnd = () => {} }) {
    this.draggables.push({ hitTest, onDrag, onDragEnd });
  }

  _onMouseDown(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    this.lastX = x;
    for (const d of this.draggables) {
      if (d.hitTest(x)) {
        this.active = d;
        break;
      }
    }
  }

  _onMouseMove(e) {
    if (!this.active) return;
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const dx = x - this.lastX;
    this.active.onDrag(dx);
    this.lastX = x;
  }

  _onMouseUp(e) {
    if (this.active) {
      this.active.onDragEnd();
      this.active = null;
    }
  }
}

function setupInfoLayerHandlers(canvas, highlightData, infoLayerId = 'infoLayer') {

    const container = document.getElementById('cvs_hl');
    const infoLayer = document.getElementById(infoLayerId);
    const infoMin = document.getElementById('info-min');
    const infoMax = document.getElementById('info-max');

    if (!container || !infoLayer || !infoMin || !infoMax) {
        console.warn('Required DOM elements for info layer not found.');
        return;
    }

    let activeHighlight = null;

    container.addEventListener('click', (event) => {
        const rect = highlightLayer.getBoundingClientRect();
        const x = event.clientX - rect.left;

        const clickedHighlight = highlightData;
        if (x >= clickedHighlight.min_sel && x <= clickedHighlight.max_sel) {
            infoLayer.style.display = 'block';
            infoLayer.style.left = `${event.pageX + 10}px`;
            infoLayer.style.top = `${event.pageY + 10}px`;
            infoMin.textContent = `Min: ${clickedHighlight.min_sel}`;
            infoMax.textContent = `Max: ${clickedHighlight.max_sel}`;
            activeHighlight = clickedHighlight;
        } else {
            infoLayer.style.display = 'none';
            activeHighlight = null;
        }
    });
}

function peaks2x(latestPeakData, fft_size, canvasWidth) {

    let x_peaks = [];

    for (let i = 0; i < latestPeakData.length; i++) {
        function binToX(binIndex) {
            return Math.floor((binIndex / fft_size) * canvasWidth);
        }
        x_peaks.push(binToX(latestPeakData[i]));
    }

    return x_peaks;
}

function draw_highlights(highlights) {

    const highlightLayer = new HighlightLayer("cvs_hl");

    for (let { x, y, label, color } of highlights) {
        highlightLayer.addHighlight(x, y, 1.0, 'rgba(255,0,0,ALPHA)');

        const highlightData = {
            min_sel: x,
            max_sel: y,
            canvas: highlightLayer.canvas
        };

        setupInfoLayerHandlers(highlightLayer.canvas, highlightData);
    }
}

// Convert interleaved complex Float32Array to Uint8Array (magnitude, 0..255)
function processBlockData(block) {

    function normalizeToUint8(block, outArray, minDb = -100, maxDb = 0) {
      const range = maxDb - minDb;
      for (let i = 0; i < block.length; i++) {
        let scaled = ((block[i] - minDb) / range) * 255;
        outArray[i] = Math.max(0, Math.min(255, Math.floor(scaled)));
      }
    }

    const floatBlock = new Float32Array(block);
    const magnitudes = new Uint8Array(fft_size);
    normalizeToUint8(floatBlock, magnitudes, -5, 30);   // make adjustable

    return magnitudes;
}

// Data generator using most recent processed buffer
function FreqDataGenerator(sampling_rate, fft_size) {

    this.rawLineTime = 1000 * fft_size / sampling_rate;
    this.sampleFreq = sampling_rate;
    this.fft_size = fft_size;

    // double buffering
    let currentBuffer = new Uint8Array(this.fft_size);

    this.getLine = () => {
        if (blockReady) {
            currentBuffer.set(latestBlockData);     // copy into buffer
            blockReady = false;
            requestBlock();                         // ask for next block right after processing
        }
        return { buffer: currentBuffer };  // always return latest
    };
}

// Start dynamic polling of new lines
function getDynamicDataBuffer(dataGen) {

    const bufferAry = [];
    let sigTime = 0;
    const sigStartTime = Date.now();

    bufferAry[0] = new Uint8Array(dataGen.fft_size);
    bufferAry[1] = new Uint8Array(dataGen.fft_size);

    function genDynamicData() {
        let sigDiff;

        const result = dataGen.getLine();  // returns { buffer }
        bufferAry[1].set(result.buffer);

        // swap
        const tmp = bufferAry[0];
        bufferAry[0] = bufferAry[1];
        bufferAry[1] = tmp;

        sigTime += dataGen.rawLineTime;
        sigDiff = (Date.now() - sigStartTime) - sigTime;

        if (playing) {
            setTimeout(genDynamicData, dataGen.rawLineTime - sigDiff);
        }
    }

    requestBlock();        // Start first fetch
    genDynamicData();      // Kick off polling loop

    return { buffer: bufferAry[0] };
}

function draw_indicia() {

    const cvs_xaxis = document.getElementById("cvs_xaxis");
    const xaxis_ctx = cvs_xaxis.getContext("2d");

    // Instantiate DragManager for frequency axis
    const dragAxis = new DragManager(cvs_xaxis);
    dragAxis.addDraggable({
      hitTest: x => Math.abs(x - cvs_xaxis.width / 2) < 6,
      onDrag: dx => {
        const deltaFreq = dx * (sampling_rate / fft_size * (fft_size / cvs_xaxis.width));
        center_freq += deltaFreq;
        draw_indicia();
      }
    });

    // Clear and prep canvas
    xaxis_ctx.clearRect(0, 0, cvs_xaxis.width, cvs_xaxis.height);
    xaxis_ctx.fillStyle = bgcolor;
    xaxis_ctx.fillRect(0, 0, cvs_xaxis.width, cvs_xaxis.height);

    // Draw center line
    const centerX = cvs_xaxis.width / 2;
    xaxis_ctx.strokeStyle = "red";
    xaxis_ctx.beginPath();
    xaxis_ctx.moveTo(centerX, 0);
    xaxis_ctx.lineTo(centerX, cvs_xaxis.height);
    xaxis_ctx.stroke();

    // Frequencies
    const min_freq_hz = center_freq - sampling_rate / 2;
    const max_freq_hz = center_freq + sampling_rate / 2;

    function freqToX(freq) {
      const df = sampling_rate / fft_size;
      return (freq - (center_freq - sampling_rate / 2)) / df;
    }

    // Draw frequency labels (simple example)
    xaxis_ctx.fillStyle = "white";
    xaxis_ctx.font = "12px sans-serif";
    for (let i = 0; i < 5; i++) {
        let freq = center_freq + (i - 2) * sampling_rate / 4;
        let x = centerX + (i - 2) * cvs_xaxis.width / 4;
        xaxis_ctx.fillText((freq / 1e6).toFixed(1) + " MHz", x - 20, 12);
    }

    const indicia = [
        { freq: min_freq_hz, label: "", color: "white" },
        { freq: max_freq_hz, label: "", color: "white" }
    ];

    const min_indicia = [];
    let step = Math.floor(cvs_xaxis.width/10);
    for (let i = 0; i < 10; i++) {
        min_indicia.push({ freq: step*i, label: "", color: "white" });
    }

    // Draw vertical lines
    for (let { freq, label, color } of indicia) {
        const x = freqToX(freq);

        // Vertical line
        xaxis_ctx.beginPath();
        xaxis_ctx.moveTo(x, 20);
        xaxis_ctx.lineTo(x, cvs_xaxis.height);
        xaxis_ctx.strokeStyle = color;
        xaxis_ctx.lineWidth = 5;
        xaxis_ctx.stroke();
    }

    for (let { freq, label, color } of min_indicia) {

        // Vertical line
        xaxis_ctx.beginPath();
        xaxis_ctx.moveTo(freq, 25);
        xaxis_ctx.lineTo(freq, cvs_xaxis.height);
        xaxis_ctx.strokeStyle = color;
        xaxis_ctx.lineWidth = 2;
        xaxis_ctx.stroke();
    }
}

function draw_spec() {

    const dataGenerator = new FreqDataGenerator(sampling_rate, fft_size);
    const dataObj = getDynamicDataBuffer(dataGenerator);

    // Matlab Jet ref: stackoverflow.com grayscale-to-red-green-blue-matlab-jet-color-scale
    const colMap = [
                [  0,   0, 128, 255], [  0,   0, 131, 255], [  0,   0, 135, 255], [  0,   0, 139, 255],
                [  0,   0, 143, 255], [  0,   0, 147, 255], [  0,   0, 151, 255], [  0,   0, 155, 255],
                [  0,   0, 159, 255], [  0,   0, 163, 255], [  0,   0, 167, 255], [  0,   0, 171, 255],
                [  0,   0, 175, 255], [  0,   0, 179, 255], [  0,   0, 183, 255], [  0,   0, 187, 255],
                [  0,   0, 191, 255], [  0,   0, 195, 255], [  0,   0, 199, 255], [  0,   0, 203, 255],
                [  0,   0, 207, 255], [  0,   0, 211, 255], [  0,   0, 215, 255], [  0,   0, 219, 255],
                [  0,   0, 223, 255], [  0,   0, 227, 255], [  0,   0, 231, 255], [  0,   0, 235, 255],
                [  0,   0, 239, 255], [  0,   0, 243, 255], [  0,   0, 247, 255], [  0,   0, 251, 255],
                [  0,   0, 255, 255], [  0,   4, 255, 255], [  0,   8, 255, 255], [  0,  12, 255, 255],
                [  0,  16, 255, 255], [  0,  20, 255, 255], [  0,  24, 255, 255], [  0,  28, 255, 255],
                [  0,  32, 255, 255], [  0,  36, 255, 255], [  0,  40, 255, 255], [  0,  44, 255, 255],
                [  0,  48, 255, 255], [  0,  52, 255, 255], [  0,  56, 255, 255], [  0,  60, 255, 255],
                [  0,  64, 255, 255], [  0,  68, 255, 255], [  0,  72, 255, 255], [  0,  76, 255, 255],
                [  0,  80, 255, 255], [  0,  84, 255, 255], [  0,  88, 255, 255], [  0,  92, 255, 255],
                [  0,  96, 255, 255], [  0, 100, 255, 255], [  0, 104, 255, 255], [  0, 108, 255, 255],
                [  0, 112, 255, 255], [  0, 116, 255, 255], [  0, 120, 255, 255], [  0, 124, 255, 255],
                [  0, 128, 255, 255], [  0, 131, 255, 255], [  0, 135, 255, 255], [  0, 139, 255, 255],
                [  0, 143, 255, 255], [  0, 147, 255, 255], [  0, 151, 255, 255], [  0, 155, 255, 255],
                [  0, 159, 255, 255], [  0, 163, 255, 255], [  0, 167, 255, 255], [  0, 171, 255, 255],
                [  0, 175, 255, 255], [  0, 179, 255, 255], [  0, 183, 255, 255], [  0, 187, 255, 255],
                [  0, 191, 255, 255], [  0, 195, 255, 255], [  0, 199, 255, 255], [  0, 203, 255, 255],
                [  0, 207, 255, 255], [  0, 211, 255, 255], [  0, 215, 255, 255], [  0, 219, 255, 255],
                [  0, 223, 255, 255], [  0, 227, 255, 255], [  0, 231, 255, 255], [  0, 235, 255, 255],
                [  0, 239, 255, 255], [  0, 243, 255, 255], [  0, 247, 255, 255], [  0, 251, 255, 255],
                [  0, 255, 255, 255], [  4, 255, 251, 255], [  8, 255, 247, 255], [ 12, 255, 243, 255],
                [ 16, 255, 239, 255], [ 20, 255, 235, 255], [ 24, 255, 231, 255], [ 28, 255, 227, 255],
                [ 32, 255, 223, 255], [ 36, 255, 219, 255], [ 40, 255, 215, 255], [ 44, 255, 211, 255],
                [ 48, 255, 207, 255], [ 52, 255, 203, 255], [ 56, 255, 199, 255], [ 60, 255, 195, 255],
                [ 64, 255, 191, 255], [ 68, 255, 187, 255], [ 72, 255, 183, 255], [ 76, 255, 179, 255],
                [ 80, 255, 175, 255], [ 84, 255, 171, 255], [ 88, 255, 167, 255], [ 92, 255, 163, 255],
                [ 96, 255, 159, 255], [100, 255, 155, 255], [104, 255, 151, 255], [108, 255, 147, 255],
                [112, 255, 143, 255], [116, 255, 139, 255], [120, 255, 135, 255], [124, 255, 131, 255],
                [128, 255, 128, 255], [131, 255, 124, 255], [135, 255, 120, 255], [139, 255, 116, 255],
                [143, 255, 112, 255], [147, 255, 108, 255], [151, 255, 104, 255], [155, 255, 100, 255],
                [159, 255,  96, 255], [163, 255,  92, 255], [167, 255,  88, 255], [171, 255,  84, 255],
                [175, 255,  80, 255], [179, 255,  76, 255], [183, 255,  72, 255], [187, 255,  68, 255],
                [191, 255,  64, 255], [195, 255,  60, 255], [199, 255,  56, 255], [203, 255,  52, 255],
                [207, 255,  48, 255], [211, 255,  44, 255], [215, 255,  40, 255], [219, 255,  36, 255],
                [223, 255,  32, 255], [227, 255,  28, 255], [231, 255,  24, 255], [235, 255,  20, 255],
                [239, 255,  16, 255], [243, 255,  12, 255], [247, 255,   8, 255], [251, 255,   4, 255],
                [255, 255,   0, 255], [255, 251,   0, 255], [255, 247,   0, 255], [255, 243,   0, 255],
                [255, 239,   0, 255], [255, 235,   0, 255], [255, 231,   0, 255], [255, 227,   0, 255],
                [255, 223,   0, 255], [255, 219,   0, 255], [255, 215,   0, 255], [255, 211,   0, 255],
                [255, 207,   0, 255], [255, 203,   0, 255], [255, 199,   0, 255], [255, 195,   0, 255],
                [255, 191,   0, 255], [255, 187,   0, 255], [255, 183,   0, 255], [255, 179,   0, 255],
                [255, 175,   0, 255], [255, 171,   0, 255], [255, 167,   0, 255], [255, 163,   0, 255],
                [255, 159,   0, 255], [255, 155,   0, 255], [255, 151,   0, 255], [255, 147,   0, 255],
                [255, 143,   0, 255], [255, 139,   0, 255], [255, 135,   0, 255], [255, 131,   0, 255],
                [255, 128,   0, 255], [255, 124,   0, 255], [255, 120,   0, 255], [255, 116,   0, 255],
                [255, 112,   0, 255], [255, 108,   0, 255], [255, 104,   0, 255], [255, 100,   0, 255],
                [255,  96,   0, 255], [255,  92,   0, 255], [255,  88,   0, 255], [255,  84,   0, 255],
                [255,  80,   0, 255], [255,  76,   0, 255], [255,  72,   0, 255], [255,  68,   0, 255],
                [255,  64,   0, 255], [255,  60,   0, 255], [255,  56,   0, 255], [255,  52,   0, 255],
                [255,  48,   0, 255], [255,  44,   0, 255], [255,  40,   0, 255], [255,  36,   0, 255],
                [255,  32,   0, 255], [255,  28,   0, 255], [255,  24,   0, 255], [255,  20,   0, 255],
                [255,  16,   0, 255], [255,  12,   0, 255], [255,   8,   0, 255], [255,   4,   0, 255],
                [255,   0,   0, 255], [251,   0,   0, 255], [247,   0,   0, 255], [243,   0,   0, 255],
                [239,   0,   0, 255], [235,   0,   0, 255], [231,   0,   0, 255], [227,   0,   0, 255],
                [223,   0,   0, 255], [219,   0,   0, 255], [215,   0,   0, 255], [211,   0,   0, 255],
                [207,   0,   0, 255], [203,   0,   0, 255], [199,   0,   0, 255], [195,   0,   0, 255],
                [191,   0,   0, 255], [187,   0,   0, 255], [183,   0,   0, 255], [179,   0,   0, 255],
                [175,   0,   0, 255], [171,   0,   0, 255], [167,   0,   0, 255], [163,   0,   0, 255],
                [159,   0,   0, 255], [155,   0,   0, 255], [151,   0,   0, 255], [147,   0,   0, 255],
                [143,   0,   0, 255], [139,   0,   0, 255], [135,   0,   0, 255], [131,   0,   0, 255],
                [  0,   0,   0,   0]
                ];

    const cvs_spec = document.getElementById('cvs_spec');
    const cvs_spec_ctx = cvs_spec.getContext("2d");
    const cvs_hl = new HighlightLayer("cvs_hl");
    const dragHl = new DragManager(cvs_hl.canvas);

    const cgo = new Cango("cvs_spec");
    cgo.clearCanvas(bgcolor);
    cgo.gridboxPadding(0);
    cgo.setWorldCoordsSVG(0, 0, cvs_spec.width, cvs_spec.height/10);

    draw_indicia();
    draw_highlights(cvs_hl, dragHl, highlights);  // mark something.

    const wf = new Waterfall(dataObj, fft_size, cvs_spec.height, "DOWN");
    wf.start();

    function draw_waveforms()
    {

        const imgObj = cvs_spec_ctx.getImageData(0,0, cvs_spec.width, cvs_spec.height);
        const pxPerLine = imgObj.width;
        var dataLine = [];

        dataLine =  dataObj.buffer;

        // Loop through each row of the canvas
        for (let row = 0; row < cvs_spec.height; row++) {
            for (let px = 0; px < pxPerLine; px++) {

                //Calculate index in the image data buffer
                let i = 4 * (row * pxPerLine + px);

                //Get the corresponding color from the color map
                let val =  dataLine[px];
                const rgba = colMap[val];

                // Set RGBA values in the image data buffer
                imgObj.data[i]     = rgba[0]; // red
                imgObj.data[i + 1] = rgba[1]; // green
                imgObj.data[i + 2] = rgba[2]; // blue
                imgObj.data[i + 3] = rgba[3]; // alpha
            }
        }

        let wfImg = new Img(wf.offScreenCvs, { imgWidth: cvs_spec.width, imgHeight: cvs_spec.height/10 });
        cgo.render(wfImg);
        cvs_hl.render();

        window.requestAnimationFrame(draw_waveforms);
    }
    draw_waveforms();
}

let playing = true;

window.addEventListener("load", function () {
    draw_spec();
});
