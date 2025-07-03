peity.defaults.line = {
    delimiter: ",",
    fill: "#777",
    height: 18,
    width: 150,
    max: -100,
    min: 0,
    stroke: "#00ff00",
    strokeWidth: 2
}

// Formatter to generate peity charts
var chartFormatter = function(cell, formatterParams, onRendered){

    var content = document.createElement("span");
    var values = cell.getValue();
    content.classList.add('line');
    content.innerHTML = values.join(",");

    // after the cell element has been added to the DOM
    onRendered(function(){
        peity(content, 'line');
    });

    return content;
};

function colorUniqId(data, splt){
    var parts = data.split(splt);
    var R = (parseInt(parts[0], 16) + parseInt(parts[1], 16)) % 255;
    var G = (parseInt(parts[2], 16) + parseInt(parts[3], 16)) % 255;
    var B = (parseInt(parts[4], 16) + parseInt(parts[5], 16)) % 255;
    return [R,G,B];
};

function averageColor([R,G,B]){
    let avg = R+G+B/3;
    return (avg > 128)? "00,00,00": "255,255,255";
};

Tabulator.extendModule("mutator", "mutators", {
    signalMutator:function(value, data, type, mutatorParams) {
        var sgnlList = [];
        for (const pt of value) {
            sgnlList.push(pt['sgnl'])
        }
        return sgnlList;
    },
});
