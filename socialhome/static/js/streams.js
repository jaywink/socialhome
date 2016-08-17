$(function () {
    if (typeof socialhomeStream !== "undefined") {
        // Correctly decide between ws:// and wss://
        var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
        var ws_path = ws_scheme + '://' + window.location.host + "/ch/streams/" + socialhomeStream + "/";
        console.log("Connecting to " + ws_path);
        var socket = new ReconnectingWebSocket(ws_path);
        var availableContent = [];

        // Handle incoming messages
        socket.onmessage = function(message) {
            // Decode the JSON
            console.log("Got message " + message.data);
            var data = JSON.parse(message.data);
            console.log(data);
            if (data.event === "new" && availableContent.indexOf(data.id) === -1) {
                availableContent.push(data.id);
                $("#new-content-count").html(availableContent.length);
                $("#new-content-container").show(100);
            } else if (data.event === "content") {
                var $grid = $('.grid'),
                    $contents,
                    ids = [];
                _.each(data.contents, function(content) {
                    var $elem = $('<div class="grid-item">' + content.rendered + '</div>');
                    $contents = $contents ? $contents.add($elem) : $elem;
                    ids.push(content.id);
                });
                availableContent = _.difference(availableContent, ids);
                if (! availableContent.length) {
                    $("#new-content-container").hide();
                }
                $("#new-content-count").html(availableContent.length);
                $grid.prepend($contents).masonry("prepended", $contents);
                // Layout Masonry after each image loads
                $grid.imagesLoaded().progress(function() {
                    $grid.masonry('layout');
                });
            }
        };

        // Helpful debugging
        socket.onopen = function () {
            console.log("Connected to notification socket");
            if (availableContent.length) {
                $("#new-content-container").show(100);
            }
            // Stream content refresh
            $("#new-content-load-link").click(function() {
                console.log("Load new content");
                var data = {
                    "action": "load_content",
                    "ids": availableContent
                };
                socket.send(JSON.stringify(data));
            });
        };
        socket.onclose = function () {
            console.log("Disconnected to notification socket");
            $("#new-content-load-link").off("click");
            $("#new-content-container").hide();
        };
    }
});
