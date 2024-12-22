const range = (start, stop, step) => Array.from({ length: (stop - start) / step + 1}, (_, i) => start + (i * step))
const slider_range = 127;

function draw_line(ctx, fx, fy, tx, ty){
    ctx.beginPath();
    ctx.moveTo(fx, fy);
    ctx.lineTo(tx, ty);
    ctx.stroke();
};

function handleSlider(slider) {

    document.querySelector('input')
        .addEventListener('input', evt => {

        const slider_output = document.getElementById(slider.id.replace('_input', '_output'));
        const canvas = document.getElementById("canvas");
        const ctx = canvas.getContext("2d");

        function updateSlider() {
            const component = slider.id.replace('_input', '');
            const text = document.getElementById('cam_slider_krnl_output')
            let stepSz = slider.value;
            text.innerHTML = slider.value;

            let hw = canvas.width/2;
            let hh = canvas.height/2;
            let hs = stepSz/2;
            let hsl = slider_range/2

            var pos_heights = range(0, canvas.height, hs);
            var pos_widths = range(0, canvas.width, hs);

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.save();

            ctx.translate(hw, hh);
            ctx.fillRect(-4, -4, 8, 8);

            for(i=0; i<2; i++){

                for (y=0; y < pos_heights.length; y++) {
                    draw_line(ctx, -canvas.height, pos_heights[y], canvas.height, pos_heights[y]);
                };

                for (x=0; x < pos_widths.length; x++) {
                    draw_line(ctx, pos_widths[x], -canvas.width,  pos_widths[x], canvas.width);
                }
                ctx.rotate(180 * Math.PI / 180);
            }
            // Restore the transform
            ctx.restore();
        }
        updateSlider();
    });
}
