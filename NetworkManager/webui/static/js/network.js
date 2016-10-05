function randNum() {
	return Math.floor((Math.random()*4)+1);
}

var nodes = new vis.DataSet([
	{id: 1, label: 'Node 1'},
	{id: 2, label: 'Node 2'},
	{id: 3, label: 'Node 3'},
	{id: 4, label: 'Node 4'},
	{id: 5, label: 'Node 5'},
]);

var edges = new vis.DataSet([
	{from: randNum(), to: randNum()},
	{from: randNum(), to: randNum()},
	{from: randNum(), to: randNum()},
	{from: randNum(), to: randNum()},
	{from: randNum(), to: randNum()},
	{from: randNum(), to: randNum()}
]);

var container = document.getElementById('mynetwork');
var data = {
	nodes: nodes,
	edges: edges
};

var options = {};
var network = new vis.Network(container, data, options);

