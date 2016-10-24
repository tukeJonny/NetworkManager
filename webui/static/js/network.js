/*
var IMG_DIR = location.origin + "/static/img/"
var nodes = [
	{id: 1, label: 'switch 1', shape: 'image', image: IMG_DIR+"switch.png"},
	{id: 2, label: 'switch 2', shape: 'image', image: IMG_DIR+"ryu.png"},
	{id: 3, label: 'switch 3'},
	{id: 4, label: 'switch 4'},
	{id: 5, label: 'switch 5'}
];
nodes = new vis.DataSet(nodes);

idx=1
var edges = [];
for(var i = 1; i <= 5; i++) {
	for(var j = i+1; j <= 5; j++) {
		edges.push({id: idx, from: i, to: j});
		idx++;
	}
}
edges = new vis.DataSet(edges);


var container = document.getElementById('mynetwork');
var data = {
	nodes: nodes,
	edges: edges
};

var options = {};
var network = new vis.Network(container, data, options);

network.on("click", function(params) {
	params.event = "[original event]";
	document.getElementById('eventSpan').innerHTML = "<h2>Click event:</h2>" + JSON.stringify(params, null, 4);
});
*/

var manager = new NetworkGraph();

manager.addNode("switch1", "switch");
manager.addNode("ryu1", "ryu");
manager.addNode("laptop1", "laptop");

for(i=0; i<3; i++) {
	for(j=i+1; j<3; j++) {
		manager.addEdge(i, j);
	}
}

manager.draw();






























