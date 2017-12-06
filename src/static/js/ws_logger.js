"use strict";

var connection = null;
var clientID = 0;

var WebSocket = WebSocket || MozWebSocket;


function connect() {
    var serverUrl = "ws://" + window.location.hostname + ":6502/logs";

    connection = new WebSocket(serverUrl);

    connection.onopen = function(evt) {
        console.log("Connected to logging service")
    };

    connection.onmessage = function(evt) {
        var msg = JSON.parse(evt.data);
        console.log(msg); // FIXME
    }
}
