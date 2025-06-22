window.addEventListener('DOMContentLoaded', () => {
    // Instantiate InfoLayer Handlers
    const highlightLayer = new HighlightLayer("cvs_hl");
    const highlightData = {};
    setupInfoLayerHandlers(highlightLayer.canvas, highlightData);
});

