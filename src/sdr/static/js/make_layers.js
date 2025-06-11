window.addEventListener('DOMContentLoaded', () => {
    // Instantiate highlight
    const highlightLayer = new HighlightLayer("cvs_hl");

    const highlightData = {
        min_sel: 0,
        max_sel: 1024,
        canvas: highlightLayer.canvas
    };

    setupInfoLayerHandlers(highlightLayer.canvas, highlightData);
});

