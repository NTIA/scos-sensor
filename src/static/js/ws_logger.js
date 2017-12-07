"use strict";

var connection = null;
var clientID = 0;

var WebSocket = WebSocket || MozWebSocket;


function connect() {
    var serverUrl = "wss://" + window.location.hostname + "/logs";

    connection = new WebSocket(serverUrl);

    connection.onopen = function(evt) {
        console.log("Connected to logging service")
    };

    connection.onmessage = function(evt) {
        var msg = JSON.parse(evt.data);
        var container_name;
        if (msg.Container.Name.substring(0, 1) == '/') {
            container_name = msg.Container.Name.substring(1);
        } else {
            container_name = msg.Container.Name;
        }
        console.log("[" + container_name + "] " + msg.Data);
    };

    window.onbeforeunload = function(evt) {
        connection.close();
    }
}


window.onload = connect();
