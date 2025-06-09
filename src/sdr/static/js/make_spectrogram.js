
const socket = io();
const fft_length = 4096;

socket.on('connect', () => {
    console.log("Socket connected");
});

// Shared buffer to hold latest block data
let latestBlockData = new Uint8Array(fft_length);           // Initialized with dummy data
let blockReady = false;

// Emit read_block
function requestBlock() {
    socket.emit('read_block');
}

// When server sends new block
socket.on('block_data', (data) => {
        if (data) {                                         // 4096 complex numbers = 8192 float32 values
        const floatArray = new Float32Array(data);
        latestBlockData = processBlockData(floatArray);     // convert to 0..255
        blockReady = true;
    } else {
        console.warn("Invalid block_data received");
    }
});


// Convert interleaved complex Float32Array to Uint8Array (magnitude, 0..255)
function processBlockData(block) {

    function normalizeToUint8(block, outArray, minDb = -100, maxDb = 0) {
      const range = maxDb - minDb;
      for (let i = 0; i < block.length; i++) {
        let scaled = ((block[i] - minDb) / range) * 255;
        outArray[i] = Math.max(0, Math.min(255, Math.floor(scaled)));
      }
    }

    const floatBlock = new Float32Array(block); // 4096 float magnitudes in dB
    const magnitudes = new Uint8Array(fft_length);
    normalizeToUint8(floatBlock, magnitudes, -100, 100);  // display anything from -90 dB to 0 dB

    return magnitudes;
}

// Data generator using most recent processed buffer
function FreqDataGenerator(sampling_rate, fft_length) {

    this.rawLineTime = 1000 * fft_length / sampling_rate;
    this.sampleFreq = sampling_rate;
    this.fft_length = fft_length;

    // double buffering
    let currentBuffer = new Uint8Array(this.fft_length);

    this.getLine = () => {
        if (blockReady) {
            currentBuffer.set(latestBlockData);  // copy into buffer
            blockReady = false;
            requestBlock();  // ask for next block right after processing
        }
        return { buffer: currentBuffer };  // always return latest
    };
}

// Start dynamic polling of new lines
function getDynamicDataBuffer(dataGen) {

    const bufferAry = [];
    let sigTime = 0;
    const sigStartTime = Date.now();

    bufferAry[0] = new Uint8Array(dataGen.fft_length);
    bufferAry[1] = new Uint8Array(dataGen.fft_length);

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
            // console.log('sigDiff: ' + sigDiff);
        }
    }

    requestBlock();        // Start first fetch
    genDynamicData();      // Kick off polling loop

    return { buffer: bufferAry[0] };
}

function drawSpectrograms() {

    const sampling_rate = 2.048e6;      // get this from config

    const center_freq = 100e6;           // get this from sdr
    const bandwidth = 100;             // from sdr

    const min_freq = center_freq - (bandwidth / 2);
    const max_freq = center_freq + (bandwidth / 2);

    const fft_bins = 2048;              // get this from config
    const spectrogram_rows = 500;       // this one

    const maxFreq = max_freq + center_freq;
    const maxTime = 20;

    const dataGenerator = new FreqDataGenerator(sampling_rate, fft_length);
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

    const cgo = new Cango("cvs");
    cgo.gridboxPadding(4, 4, 4, 4);
    cgo.setWorldCoordsRHC(0, -maxTime, maxFreq, maxTime)

    // new BoxAxes(xmin, xmax, ymin, ymax [, options])
    const baxes = new BoxAxes(min_freq, max_freq, -Infinity, 0, {
//        xUnits:"Hz",
//        yUnits:"sec",
//        xTickInterval:"auto",
//        yTickInterval:"auto",
        strokeColor: "#000000",
        fillColor: '#000000'
    });

    cgo.render(baxes);

//    xax = new Xaxis(min_freq, max_freq, []);
//        yOrigin: 0,
//        xUnits:"Hz",
//        xTickInterval:"auto",
//        strokeColor: "#000000",
//        fillColor: '#000000'
//    });
    //cgo.render(xax);

    console.log('center_freq: ' + center_freq + ' bandwidth: ' + bandwidth + ' min_freq:' + min_freq + ' max_freq' + max_freq);

    const wf = new Waterfall(dataObj, fft_bins, spectrogram_rows, "DOWN");
    wf.start();

    function draw_waveforms()
    {

        const canvas = document.getElementById('cvs');
        const ctx = canvas.getContext("2d");
        const imgObj = ctx.getImageData(0,0, canvas.width, canvas.height);
        const pxPerLine = imgObj.width;
        var dataLine = [];

        dataLine =  dataObj.buffer;

        // Loop through each row of the canvas
        for (let row = 0; row < canvas.height; row++) {
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

        let wfImg = new Img(wf.offScreenCvs, { imgWidth: maxFreq, imgHeight: maxTime });
        cgo.render(wfImg);

        window.requestAnimationFrame(draw_waveforms);
    }
    draw_waveforms();
}

let playing = true;

window.addEventListener("load", function () {
    drawSpectrograms();
});

