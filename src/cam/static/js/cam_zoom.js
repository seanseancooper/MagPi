let currentZoom = 1;
let minZoom = 1;
let maxZoom = 3;
let stepSize = .01;

let container = document.getElementById('videomagnifier');

container.addEventListener('wheel', function (event) {
	// Zoom in or out based on the scroll direction
	let direction = event.deltaY > 0 ? -1 : 1;
	zoomImage(direction);
});

function zoomImage(direction) {
	let newZoom = currentZoom + direction * stepSize;

	// Limit the zoom level to the minimum and maximum values
	if (newZoom < minZoom || newZoom > maxZoom) {
		return;
	}

	currentZoom = newZoom;

	// Update the CSS transform of the image to scale it
	let image = document.querySelector('#_video');
	image.style.transform = 'scale(' + currentZoom + ')';
}
