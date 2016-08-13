$(function () {
    if (typeof socialhomeStream !== "undefined") {
        // Correctly decide between ws:// and wss://
        var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
        var ws_path = ws_scheme + '://' + window.location.host + "/ch/streams/" + socialhomeStream + "/";
        console.log("Connecting to " + ws_path);
        var socket = new ReconnectingWebSocket(ws_path);
        // Helpful debugging
        socket.onopen = function () {
            console.log("Connected to notification socket");
        };
        socket.onclose = function () {
            console.log("Disconnected to notification socket");
        };
    }
});
