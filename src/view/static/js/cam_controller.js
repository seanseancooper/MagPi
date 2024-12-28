
function setsHeaders(xhttp) {
    xhttp.setRequestHeader('Access-Control-Allow-Origin', 'localhost:*');
    xhttp.setRequestHeader('Access-Control-Allow-Methods', 'POST, GET');
    xhttp.setRequestHeader('Content-Type', 'text/html');
    xhttp.setRequestHeader('Access-Control-Allow-Headers', 'Content-Type, Access-Control-*, majic-color');
}

function load_video(){
    var _video = document.getElementById("_video");

    while (_video.src != "http://localhost:6100/stream") {
        _video.src = "http://localhost:6100/stream";
    }
}

function fore_aft(button){
    // changes fore/aft view
    var xhttp = new XMLHttpRequest();
    xhttp.open('POST', '{{ url_for('.index')}}view/' + button.value);
    setsHeaders(xhttp);
    xhttp.send(); // no response

    button.value = (button.value == "FORE")? "AFT": "FORE";
    document.getElementById("fore_aft_button").innerHTML = button.value.split('')[0];
    document.getElementById("fore_aft_button").classList.value = "fore_aft_button";

    setTimeout(function() {
        load_video();
    }, 10);
}

function cam_multibutton(button){
    // set symbology & analysis
    const xhttp = new XMLHttpRequest();
    xhttp.open('POST', "{{ url_for('.index')}}multibutton/" + button.value);
    setsHeaders(xhttp);
    xhttp.send();

    xhttp.onload = function() {
        const resp = xhttp.response;
        document.getElementById("multi_button").value = resp;
        document.getElementById("multi_button_text").innerHTML = resp;
    }
}

function handleCropper(cropper) {
    // send crop
    const cropper_output = document.getElementById(cropper.id.replace('_input', '_output'));

    function updateCropper() {
        var component = cropper.id.replace('_input', '');

        const xhttp = new XMLHttpRequest();
        xhttp.open('POST', '{{ url_for('.index')}}plugin/' + component + "/" + cropper.value);
        setsHeaders(xhttp);
        xhttp.send();

        xhttp.onload = function() {
            if (xhttp.response == "OK"){
                var j = JSON.parse(cropper.value);
                cropper_output.innerText = "x:" + j['x'] +
                                          " y:" + j['y'] +
                                          " w:" + j['w'] +
                                          " h:" + j['h'];
            }
        };
    }

    updateCropper();
}

function handleSlider(slider) {
    // handle continous
    const slider_output = document.getElementById(slider.id.replace('_input', '_output'));

    function updateSlider() {
        var component = slider.id.replace('_input', '');
        //draw_grid([slider.value, slider.value], '#00F', 1);
        const xhttp = new XMLHttpRequest();
        xhttp.open('POST', '{{ url_for('.index')}}plugin/' + slider.id.replace('cam_slider_', '').replace('_input', '') + "/" + parseFloat(slider.value));
        setsHeaders(xhttp);
        xhttp.send();

        xhttp.onload = function() {
            if (xhttp.response == "OK") {
                slider_output.innerText = slider.value;
                slider.addEventListener('input', updateSlider);
            }
        };
    }

    updateSlider();
}

function handleGridSlider(slider) {
    const grid = document.getElementById("grid");


    document.querySelector('#cam_slider_krnl_input')
        .addEventListener('input', evt => {

        const slider_output = document.getElementById(slider.id.replace('_input', '_output'));
        grid.style.setProperty('display','block');
        const ctx = grid.getContext("2d");
        const range = (start, stop, step) => Array.from({ length: (stop - start) / step + 1}, (_, i) => start + (i * step))
        const slider_range = 127;

        function draw_line(ctx, fx, fy, tx, ty){
            ctx.lineWidth = 1;
            ctx.strokeStyle = "gray";

            ctx.beginPath();
            ctx.moveTo(fx, fy);
            ctx.lineTo(tx, ty);
            ctx.stroke();
        };

        function updateSlider() {
            const component = slider.id.replace('_input', '');
            const text = document.getElementById('cam_slider_krnl_output');

            let stepSz = slider.value;
            text.innerHTML = slider.value;

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
                    draw_line(ctx, -grid.height, pos_heights[y], grid.height, pos_heights[y]);
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
    grid.style.setProperty('display','none');
}

function handleCheckBox(checkbox) {
    // handle binary
    const cb_output = document.getElementById(checkbox.id.replace('_input', '_output'));

    function updateCheckBox() {
        var component = checkbox.id.replace('_input', '');

        const xhttp = new XMLHttpRequest();
        xhttp.open('POST', '{{ url_for('.index')}}plugin/' + checkbox.id.replace('cam_checkbox_', '').replace('_input', '') + "/" + checkbox.checked);
        setsHeaders(xhttp);
        xhttp.send();

        xhttp.onload = function() {
            if (xhttp.response == "OK") {
                cb_output.innerText = (checkbox.checked)? "ON": "OFF";
            }
        };
    }

    updateCheckBox();
}

function cam_snap(){
    //  creates still image of current view
    const xhttp = new XMLHttpRequest();
    xhttp.open('POST', '{{ url_for('.index')}}snap');
    setsHeaders(xhttp);
    xhttp.send();

    // on response, run the videobutton animation
    xhttp.onload = function() {
        const resp = xhttp.response;
        var snapButton = document.getElementById('snap_button_text');

        if (resp == "OK"){
            snapButton.classList.value = "snap_button_text";
            snapButton.innerHTML = "x";
            setTimeout(function() {
                snapButton.innerHTML = "+";
            }, 250);
        }
    };
};
