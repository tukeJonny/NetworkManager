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






























