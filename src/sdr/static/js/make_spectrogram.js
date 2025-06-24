class DragManager {

    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext("2d", {willReadFrequently: true});
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

    render(ctx) {
        ctx.save();
        ctx.globalAlpha = this.alpha;
        ctx.fillStyle = this.color;
        ctx.fillRect(this._min_sel, 0, this._max_sel - this._min_sel, ctx.canvas.height);
        ctx.restore();
    }
}

class HighlightLayer {

	constructor(canvasId) {
		this.canvas = document.getElementById(canvasId);
		this.ctx = this.canvas.getContext("2d", {willReadFrequently: true});
		this.highlights = [];
	}

	addHighlight(min_sel, max_sel, alpha, color) {
		this.highlights.push(new Highlight(min_sel, max_sel, alpha, color));
	}

	render() {
		this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
		this.highlights.forEach(h => h.render(this.ctx));
	}
}

const socket = io();
const nfft = 4096;                                          // size of PSD. aka NFFT
//const samp_scan = nfft*16;                                // number of samples per scan
const lineRate = 10;
const sampling_rate = 2.048e6;                              // matches sdr
let center_freq = 97e6;                                     // matches sdr

let uint8magnitudes = new Uint8Array(nfft);                 // Shared buffer to hold latest block data
let blockReady = false;
let latestPeakData = new Uint8Array(1024);                  // Hold latest peak data
const signalMetadataMap = new Map();                        // key: highlight ID or position, value: metadata

let bgcolor = "#000099";
let normBounds = { minDb: -5, maxDb: 100 };
let highlights = [
      { min_sel: 462, max_sel: 565, alpha: 0.4, color: "green" } // 1k bandwidth
];

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

socket.on('connect', () => {
	console.log("Socket connected");
});

socket.on('block_data', (block) => {
	if (block) {                                            // 16384 complex32 numbers
		const floatArray = new Float32Array(block);         // 4096 float32 values
		//requestPeaks();                                   // MOVE/OMIT trigger peaks for block
		uint8magnitudes = processFloat32Data(floatArray);   // convert 4096 float32 to 4096 0..255
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

function requestBlock() {
	socket.emit('read_block');
}

function requestPeaks() {
	socket.emit('get_peaks');
}

function requestMetadata() {
	socket.emit('meta_data');
}

function freqToX(freq) {
    const df = sampling_rate / nfft;
    return (freq - (center_freq - sampling_rate / 2)) / df;
}

function updateSliderBounds() {
    let minVal = parseInt(rangeMin.value);
    let maxVal = parseInt(rangeMax.value);

    if (minVal > maxVal) {
        minVal = maxVal;
        rangeMin.value = minVal;
    }

    normBounds.minDb = minVal;
    normBounds.maxDb = maxVal;

    document.getElementById("rangeMinDb").textContent = `${minVal} dB`;
    document.getElementById("rangeMaxDb").textContent = `${maxVal} dB`;

}

function processFloat32Data(floatData) {

	function normalizeToUint8(floatData, outArray, minDb = -100, maxDb = 100) {
		const range = maxDb - minDb;

		for (let i = 0; i < floatData.length; i++) {
			let scaled = ((floatData[i] - minDb) / range) * 255;
			outArray[i] = Math.max(0, Math.min(255, Math.floor(scaled)));
		}
	}

	const magnitudes = new Uint8Array(nfft);
	normalizeToUint8(floatData, magnitudes, normBounds.minDb, normBounds.maxDb);

	return magnitudes;
}

function displayElapsedTime(generatorInstance, elementId) {
	setInterval(() => {
		const elapsedMs = generatorInstance.getElapsedTime();
		const seconds = (elapsedMs / 1000).toFixed(2);
		document.getElementById(elementId).textContent = `Elapsed Time: ${seconds} sec`;
	}, 10);
}

function FreqDataGenerator(sampling_rate, nfft) {

	this.rawLineTime = 1000 * nfft / sampling_rate;
	this.sampleFreq = sampling_rate;
	this.nfft = nfft;

	// double buffering
	let currentBuffer = new Uint8Array(this.nfft);

	this.getLine = () => {
		if (blockReady) {
			currentBuffer.set(uint8magnitudes);     // 4096 magnitudes into buffer
			blockReady = false;
			requestBlock();                         // ask for next block right after processing
		}
		return { buffer: currentBuffer };  // always return latest
	};
}

function CountingFreqDataGenerator(sampling_rate, nfft) {
	this.rawLineTime = 1000 * nfft / sampling_rate; // 2 ms per FFT block
	this.sampleFreq = sampling_rate;
	this.nfft = nfft;

	let currentBuffer = new Uint8Array(this.nfft);

	// Time tracking
	let blockCount = 0;
	this.startTime = performance.now();

	// External access to time
	this.getElapsedTime = () => {
		return blockCount * this.rawLineTime; // in ms
	};

	this.getLine = () => {
		if (blockReady) {
			currentBuffer.set(uint8magnitudes);     // 4096 magnitudes into buffer
			blockCount++;
			// console.log('blockCount: ' + blockCount + ' getElapsedTime:' + this.getElapsedTime() );
			blockReady = false;
			requestBlock();                         // ask for next block right after processing
		}
		return { buffer: currentBuffer };
	};
}

function getDynamicDataBuffer(dataGen) {
    const sharedBuffer = new Uint8Array(dataGen.nfft);

    function genDynamicData() {
        const result = dataGen.getLine();

        if (
            result &&
            result.buffer instanceof Uint8Array &&
            result.buffer.length === dataGen.nfft
        ) {
            sharedBuffer.set(result.buffer);
        }
        let to = dataGen.rawLineTime * lineRate;

        setTimeout(genDynamicData, to);
    }

    requestBlock();
    genDynamicData();

    return { buffer: sharedBuffer };
}

//function getDynamicDataBuffer(dataGen) {
//
//	const bufferAry = [];
//	let sigTime = 0;
//	const sigStartTime = Date.now();
//
//	bufferAry[0] = new Uint8Array(dataGen.nfft);
//	bufferAry[1] = new Uint8Array(dataGen.nfft);
//
//	function genDynamicData() {
//		let sigDiff;
//
//		const result = dataGen.getLine();  // returns { buffer }
//		bufferAry[1].set(result.buffer);
//
//		// swap
//		const tmp = bufferAry[0];
//		bufferAry[0] = bufferAry[1];
//		bufferAry[1] = tmp;
//
//		sigTime += dataGen.rawLineTime;
//		sigDiff = (Date.now() - sigStartTime) - sigTime;
//
//		setTimeout(genDynamicData, dataGen.rawLineTime - sigDiff);
//	}
//
//	requestBlock();        // Start first fetch
//	genDynamicData();      // Kick off polling loop
//
//	return { buffer: bufferAry[0] };
//}

//function calc_params(){
//
//    function calculateFftParametersForFrameRate({ sampleRate, fftSize, frameRate }) {
//        // Sanity check
//        if (frameRate <= 0) {
//            throw new Error("Frame rate must be positive");
//        }
//
//        // Time between frames in seconds
//        const timeBetweenFrames = 1.0 / frameRate;
//
//        // Total samples that need to be processed per frame
//        const samplesPerFrame = Math.floor(timeBetweenFrames * sampleRate);
//
//        // Ensure samples per frame is enough to compute at least one FFT
//        if (samplesPerFrame < fftSize) {
//            throw new Error(
//                `Frame rate ${frameRate} too high for nfft ${fftSize} at sample rate ${sampleRate}`
//            );
//        }
//
//        // Maximize the number of FFTs we can fit within the frame
//        const numFftsPerFrame = Math.max(1, Math.floor(samplesPerFrame / fftSize));
//
//        // Calculate fft_step based on spacing FFTs evenly
//        const fftStep = Math.floor(samplesPerFrame / numFftsPerFrame);
//
//        return {
//            frameRate: frameRate,
//            fftSize: fftSize,
//            fftStep: fftStep,
//            samplesPerFrame: samplesPerFrame,
//            numFftsPerFrame: numFftsPerFrame,
//            timeBetweenFramesSec: timeBetweenFrames,
//        };
//    }
//
//    const config = {
//        sampling_rate: sampling_rate,
//        nfft: nfft,
//        lineRate: lineRate
//    };
//
//    const fftParams = calculateFftParametersForFrameRate(config);
//    console.log(fftParams);
//}

function getSelectedSignalId() {
    return window.selectedSignalId || 'default_signal';
}

function emitControlCommand(commandName) {
    const selectedSignalId = getSelectedSignalId(); // Replace with actual logic to identify selected signal
        socket.emit('control_command', {
            command: commandName,
            signal_id: selectedSignalId
        });
}

//function updateInfoDisplay(metadata) {
//    document.getElementById("info_label").textContent = metadata.label || "Unknown";
//    document.getElementById("info_freq").textContent = `${(metadata.center_freq / 1e6).toFixed(3)} MHz`;
//    document.getElementById("info_bw").textContent = `${(metadata.bandwidth / 1e3).toFixed(1)} kHz`;
//    document.getElementById("info_mod").textContent = metadata.modulation || "—";
//    document.getElementById("info_snr").textContent = `${metadata.snr.toFixed(1)} dB`;
//}

function handleGridSlider(slider) {
    const grid = document.getElementById("grid");

    document.querySelector('#grid_slider_input')
        .addEventListener('input', evt => {

        const slider_output = document.getElementById(slider.id.replace('_input', '_output'));
        grid.style.setProperty('display','block');
        grid.style.setProperty('opacity',1);
        const ctx = grid.getContext("2d");
        const range = (start, stop, step) => Array.from({ length: (stop - start) / step + 1}, (_, i) => start + (i * step))
        const slider_range = 127;

        function draw_line(ctx, fx, fy, tx, ty){
            ctx.lineWidth = 1;
            ctx.strokeStyle = "white";

            ctx.beginPath();
            ctx.moveTo(fx, fy);
            ctx.lineTo(tx, ty);
            ctx.stroke();
        };

        function updateSlider() {
            const component = slider.id.replace('_input', '');
            //const text = document.getElementById('cam_slider_krnl_output');

            let stepSz = slider.value;
            //text.innerHTML = slider.value;

            let hw = grid.width/2;
            let hh = grid.height/2;
            let hs = stepSz/2;
            let hsl = slider_range/2

            var pos_heights = range(0, grid.height, hs);
            var pos_widths = range(0, grid.width, hs);

            ctx.clearRect(0, 0, grid.width, grid.height);
            ctx.save();

            ctx.translate(hw, hh);
            ctx.fillRect(-4, -4, 8, 8);

            for(i=0; i<2; i++){

                for (y=0; y < pos_heights.length; y++) {
                    draw_line(ctx, -grid.width, pos_heights[y], grid.width, pos_heights[y]);
                };

                for (x=0; x < pos_widths.length; x++) {
                    draw_line(ctx, pos_widths[x], -grid.width,  pos_widths[x], grid.width);
                }
                ctx.rotate(180 * Math.PI / 180);
            }
            // Restore the transform
            ctx.restore();
        }
        updateSlider();
    });

    // fade the grid
    setTimeout(function(){
        var fadeEffect = setInterval(function () {
            if (!grid.style.opacity) {
                grid.style.opacity = 1;
            }
            if (grid.style.opacity > 0) {
                grid.style.opacity -= 0.02;
            } else {
                clearInterval(fadeEffect);
                grid.style.setProperty('display','none');  // get grid out of the way of mouse.
            }
        }, 20);
    }, 1.5);

}

function setupInfoLayerHandlers(canvas, highlight, infoLayerId = 'infoLayer') {

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
        const x = event.clientX - canvas.getBoundingClientRect().left;

        if (x >= highlight.min_sel && x <= highlight.max_sel) {
            infoLayer.style.display = 'block';
            activeHighlight = highlight;
        } else {
            infoLayer.style.display = 'none';
            activeHighlight = null;
        }
    });
}

function draw_spec() {

    const cgo = new Cango("cvs_spec");
    const cvs_spec = document.getElementById('cvs_spec');
    const cvs_xaxis = document.getElementById("cvs_xaxis");
    const cvs_hl = new HighlightLayer("cvs_hl");
    const hl_drag = new DragManager(cvs_hl.canvas); // for highlights
    const dragAxis = new DragManager(cvs_xaxis);	// for center frequency
    const cvs_spec_ctx = cvs_spec.getContext("2d", {willReadFrequently: true});
    const cvs_xaxis_ctx = cvs_xaxis.getContext("2d", {willReadFrequently: true});

	// Frequencies
	const centerX = cvs_xaxis.width / 2;
	const min_freq_hz = center_freq - sampling_rate / 2;
	const max_freq_hz = center_freq + sampling_rate / 2;

    const countingDataGenerator = new CountingFreqDataGenerator(sampling_rate, nfft);
    const dataObj = getDynamicDataBuffer(countingDataGenerator);
    displayElapsedTime(countingDataGenerator, 'elapsedTimeDisplay');

    const wf = new Waterfall(dataObj, nfft, cvs_spec.height, "DOWN", {lineRate: lineRate}); // cvs_spec.height*time_compression: 1.0... 2.0
    wf.start();

	cgo.clearCanvas(bgcolor);
	cgo.setWorldCoordsSVG(0, 0, cvs_spec.width/4, cvs_spec.height);
	//cgo.setWorldCoordsRHC(0, 0, cvs_spec.width, cvs_spec.height/2);

// Clear and prep canvas
	cvs_xaxis_ctx.clearRect(0, 0, cvs_xaxis.width, cvs_xaxis.height);
	//cvs_xaxis_ctx.fillRect(0, 0, cvs_xaxis.width, cvs_xaxis.height);

    function draw_indicia() {
        const ctx = cvs_xaxis.getContext("2d");
        cvs_xaxis_ctx.clearRect(0, 0, cvs_xaxis.width, cvs_xaxis.height);

        // Draw center line
        cvs_xaxis_ctx.strokeStyle = "red";
        cvs_xaxis_ctx.lineWidth = 10;
        cvs_xaxis_ctx.beginPath();
        cvs_xaxis_ctx.moveTo(centerX, 0);
        cvs_xaxis_ctx.lineTo(centerX, cvs_xaxis.height);

        cvs_xaxis_ctx.stroke();

        // Draw frequency labels (simple example)
        cvs_xaxis_ctx.fillStyle = "white";
        cvs_xaxis_ctx.font = "12px sans-serif";

        for (let i = 0; i < 5; i++) {
            let freq = center_freq + (i - 2) * sampling_rate / 4;
            let x = centerX + (i - 2) * cvs_xaxis.width / 4;
            cvs_xaxis_ctx.fillText((freq / 1e6).toFixed(1) + " MHz", x - 20, 12);
        }
    }

	dragAxis.addDraggable({
        hitTest: x => Math.abs(x - centerX) < 6,
        onDrag: dx => {
            const deltaFreq = dx * (sampling_rate / nfft * (nfft / cvs_xaxis.width));
            center_freq += deltaFreq;
            draw_indicia();
        }
	});

	draw_indicia();

    highlights.forEach(h => {
        cvs_hl.addHighlight(h.min_sel, h.max_sel, h.alpha, h.color);
        const [hlInstance] = cvs_hl.highlights.slice(-1);

        hl_drag.addDraggable({
            hitTest: x => Math.abs(x - hlInstance.min_sel) < 6,
            onDrag: dx => {
              hlInstance.min_sel = Math.max(0, hlInstance.min_sel + dx);
              cvs_hl.render();
            }
        });

        hl_drag.addDraggable({
            hitTest: x => Math.abs(x - hlInstance.max_sel) < 6,
            onDrag: dx => {
              hlInstance.max_sel = Math.max(hlInstance.min_sel + 1, hlInstance.max_sel + dx);
              cvs_hl.render();
            }
        });

        setupInfoLayerHandlers(cvs_hl.canvas, hlInstance);
    });

	function draw_waveforms()
	{
		const imgObj = cvs_spec_ctx.getImageData(0,0, cvs_spec.width/4, cvs_spec.height/2);
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

		let wfImg = new Img(wf.offScreenCvs, { imgWidth: cvs_spec.width/4, imgHeight: cvs_spec.height });

		cgo.render(wfImg);
		cvs_hl.render();

		window.requestAnimationFrame(draw_waveforms);
	}
	draw_waveforms();
}

window.addEventListener("load", function () {
	draw_spec();
});
