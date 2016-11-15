var manager = new NetworkGraph();

manager.addNode(0xabc, "switch1", "switch");
manager.addNode(0xabd, "ryu1", "ryu");
manager.addNode(0xabe, "laptop1", "host");

for(i=0; i<3; i++) {
	for(j=i+1; j<3; j++) {
		manager.addEdge(i, j);
	}
}

manager.draw();






























