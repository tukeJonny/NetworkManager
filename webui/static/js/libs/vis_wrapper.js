//NetworkManager用に特化したVis.jsのラッパーライブラリ
//
//Todo:
//エッジの追加が大変なので、もうちょっと楽にしたい
//JSONを読み込んで、描画できるようにする
//余裕があれば、パケットを送るなどのアニメーションも加えてみる

////////////////////////////// Helpers //////////////////////////////
var inherits = function(childCtor, parentCtor) {
	//Constructor
	function tempCtor() {};
	tempCtor.prototype = parentCtor.prototype;
	childCtor.superClass_ = parentCtor.prototype;
	childCtor.prototype = new tempCtor();

	//Override
	childCtor.prototype.constructor = childCtor;
};

function node2edge(fromNode, toNode) {
    var infrom = {};
    console.log("fromNode="+String(fromNode)+",toNode="+String(toNode));
    for(var i = 0; i < fromNode.edges.length; i++) {
        infrom[fromNode.edges[i].id] = true;
    }
    console.log(infrom);
    for(var i = 0; i < toNode.edges.length; i++) {
        if(infrom[toNode.edges[i].id]) {
            return toNode.edges[i];
        }
    }

}

////////////////////////////// Components //////////////////////////////
//Base class
var Component = function(id, label) {
	this.id = id;
	this.IMG_DIR = location.origin+"/static/img/"
}

Component.prototype.getImageURI = function(img_name) {
	return this.IMG_DIR+img_name+".png";
};

//Node class
var Node = function(id, label) {
	Component.call(this, id);
	this.label = label;

};
inherits(Node, Component);

Node.prototype.addImage = function(img_name) {
	this.shape = "image";
	this.image = this.getImageURI(img_name);
};

Node.prototype.getNode = function() {
    var node = {
        id: this.id,
        label: this.label,
    };
    if(this.shape == "image" && this.image !== undefined) {
        node["shape"] = this.shape;
        node["image"] = this.image;
    }
    return node;
}

//Edge class
var Edge = function(id) {
	Component.call(this, id);
	this.from = undefined;
	this.to = undefined;
}
inherits(Edge, Component);

Edge.prototype.putEdge = function(from, to) {
	if(this.from === undefined && this.to === undefined) {
		this.from = from;
		this.to = to;
	} else {
		console.log("already set parameter from and to.");
	}
};

Edge.prototype.getEdge = function() {
	if(this.from === undefined || this.to === undefined) {
		console.log("Please set from and to!");
		return;
	}
	var edge = {
		id: this.id,
		from: this.from,
		to: this.to
	};
	return edge;
}

////////////////////////////// NetworkManager本体 //////////////////////////////
//NetworkGraphクラス
//グラフを描画するオブジェクト
var NetworkGraph = function(wsurl) {
	this.container_id = "mynetwork";
	this.nodes = [];
	this.edges = [];
	this.options = {};

	this.node_id = 0; //AUTO INCREMENT
	this.edge_id = 0; //AUTO INCREMENT

	this.table = {
	    switches: {
	        //datapath_id -> id
	    },
	    hosts: {
	        //ip addr -> id
	    }
	};

	//WebSocket
	if(wsurl !== undefined) {
		var socket = new WebSocket(wsurl);
		var wsres;
		socket.onopen = function() {
		    console.log("Open.");
		    socket.send("hello");
		};
		socket.onmessage = function() {
	        try {
	           wsres = $.parseJSON(message.data);
	        } catch(e) {
	           console.log("Failed to receive Websocket message.");
	        }
	        this.prototype.readJson(wsres);
		}
	} else {
		console.log("No wsurl. websocket is disabled.");
	}
};

//Methods
//addNode()メソッド。スイッチやRyuなどのノードを追加する
NetworkGraph.prototype.addNode = function(label, img_name) {
	var id = this.node_id;

	var node = new Node(id, label);
	if(img_name !== undefined) { node.addImage(img_name); }

	this.nodes.push(node.getNode());
	console.log(node.getNode());
	this.node_id++;
	return id;
}

//addEdge()メソッド。fromからtoにエッジを貼る
NetworkGraph.prototype.addEdge = function(from, to) {
	var id = this.edge_id;

	var edge = new Edge(id);
	edge.putEdge(from, to);

	this.edges.push(edge.getEdge());
	console.log(edge.getEdge());
	this.edge_id++;
	return id;
}

//グラフのオプションを追加する。key-value形式。
NetworkGraph.prototype.addOption = function(key, val) {
	this.options[key] = val;
}

//描画を開始する
NetworkGraph.prototype.draw = function() {
	var container = document.getElementById(this.container_id);
	console.log("DEBUG: Node");
	console.log(this.nodes);
	console.log("DEBUG: Edge");
	console.log(this.edges);
	//var nodes = new vis.DataSet(this.nodes);
	//var edges = new vis.DataSet(this.edges);

	var data = {
		nodes: this.nodes,
		edges: this.edges
	};
	this.network = new vis.Network(container, data, this.options);

	//events
	this.network.on("click", function(params) {
	    params.event = "[original event]";
	    document.getElementById('eventSpan').innerHTML = "<h3>Click event:</h2>" + JSON.stringify(params, null, 4);
	})
}

//受け取ったJSONに対して、適切な処理を施す。
NetworkGraph.prototype.readJson = function(json) {
    //パケットの送信
    //スイッチの追加
    //スイッチの削除
    //ホストの追加
    //ホストの削除
    //フロールール追加
    //Packet-Inされたパケットのデータを解析して、sharkパネルに表示
    console.log("We're received message -> " + String(wsres));
}

//コントローラに対してWebsocketのメッセージを送信
NetworkGraph.prototype.wssend = function(message) {
	return;
}

//labelで送れるようにするといい？(ブラウザから操作した感じ)
//APIで操作する際に何がいいか
NetworkGraph.prototype.send = function(from, to) {
    var fromNode = this.network.body.nodes[from];
    var toNode = this.network.body.nodes[to];
    var edge = node2edge(fromNode, toNode).id;
    var isBackward = fromNode.id > toNode.id

    this.network.animateTraffic([{edge: edge, trafficSize: 5, isBackward: isBackward}])
}
