$(function () {
    /*
     * Handle stream updates
     *
     * Connect to backend via a websocket. Listen to new content for the current stream.
     * Push new content to the view when user requests it.
     *
     */
    var view = {
        showNewLabel: function() {
            $("#new-content-container").show(100);
        },

        hideNewLabel: function() {
            $("#new-content-container").hide();
        },

        updateNewLabelCount: function(count) {
            $("#new-content-count").html(count);
        },

        createContentElem: function(content) {
            return $('<div class="grid-item">' + content + '</div>');
        },

        addContentToGrid: function($contents) {
            var $grid = $('.grid');
            $grid.prepend($contents).masonry("prepended", $contents);
            // Layout Masonry after each image loads
            $grid.imagesLoaded().progress(function () {
                $grid.masonry('layout');
            });
        },

        scrollToTop: function() {
            window.scrollTo(0, 0);
        },
    };

    var controller = {
        availableContent: [],

        init: function() {
            this.socket = this.createConnection();
            this.socket.onmessage = this.handleMessage;
            this.socket.onopen = this.handleSocketOpen;
            this.socket.onclose = this.handleSocketClose;
        },

        createConnection: function() {
            // Correctly decide between ws:// and wss://
            var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws",
                ws_path = ws_scheme + '://' + window.location.host + "/ch/streams/" + socialhomeStream + "/";
            return new ReconnectingWebSocket(ws_path);
        },

        handleSocketOpen: function() {
            if (controller.availableContent.length) {
                view.showNewLabel();
            }
            // Stream content refresh
            $("#new-content-load-link").click(controller.getContent);
        },

        handleSocketClose: function() {
            $("#new-content-load-link").off("click");
            view.hideNewLabel();
        },

        handleMessage: function(message) {
            var data = JSON.parse(message.data);
            if (data.event === "new" && controller.availableContent.indexOf(data.id) === -1) {
                controller.availableContent.push(data.id);
                view.updateNewLabelCount(controller.availableContent.length);
                view.showNewLabel();

            } else if (data.event === "content") {
                var $contents,
                    ids = [];

                _.each(data.contents, function (content) {
                    var $elem = view.createContentElem(content.rendered);
                    $contents = $contents ? $contents.add($elem) : $elem;
                    ids.push(content.id);
                });

                controller.availableContent = _.difference(controller.availableContent, ids);
                if (! controller.availableContent.length) {
                    view.hideNewLabel();
                }
                view.updateNewLabelCount(controller.availableContent.length);
                view.addContentToGrid($contents);
            }
        },

        getContent: function() {
            var data = {
                "action": "load_content",
                "ids": controller.availableContent
            };
            controller.socket.send(JSON.stringify(data));
            view.scrollToTop();
        }
    };

    if (typeof socialhomeStream !== "undefined") {
        controller.init();
    }
});
