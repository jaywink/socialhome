describe("Streams", function() {
    before(function () {
        window.mockServer = new window.MockServer('ws://127.0.0.1:'+runserverPort+'/ch/streams/foobar/');
        window.WebSocket = window.MockWebSocket;
        window.mockServer.on('connection', function () {
            window.connectionSuccess = true;
        });
        window.mockServer.on('message', function (data) {
            window.mockMessage = data;
        });
    });

    describe("websocket", function() {
        context("on stream page", function () {
            before(function () {
                window.socialhomeStream = "foobar";
            });

            it("connects", function (done) {
                setTimeout(function () {
                    expect(window.connectionSuccess).to.be.true;
                    done();
                }, 500);
            });

            after(function () {
                window.socialhomeStream = undefined;
                window.connectionSuccess = false;
            });
        });

        context("not on stream page", function () {
            it("doesn't connect", function (done) {
                setTimeout(function () {
                    expect(window.connectionSuccess).to.be.false;
                    done();
                }, 500);
            });
        });
    });

    describe("content", function() {
        before(function() {
            window.socialhomeStream = "foobar";
            window.mockMessage = undefined;
        });

        context("fetching", function() {
            before(function() {
                $("#new-content-container").show();
            });

            it("makes websocket call on new content load link click", function(done) {
                $("#new-content-load-link").trigger("click");
                setTimeout(function () {
                    expect(window.mockMessage).to.eq('{"action":"load_content","ids":[]}');
                    done();
                }, 500);
            });

            after(function() {
                $("#new-content-container").hide();
            });
        });

        context("receiving", function() {
            it("shows new content label on new message", function(done) {
                window.mockServer.send('{"event": "new", "id": 1}');
                setTimeout(function () {
                    expect($("#new-content-container:visible").length).to.eq(1);
                    done();
                }, 500);
            });

            it("adds new content to grid on content message", function(done) {
                var message = {
                    event: "content",
                    contents: [{
                        id: 1, rendered: "adds new content", humanized_timestamp: "2 minutes ago",
                        formatted_timestamp: "2017-01-02 10:11:12+00:00"
                    }]
                };
                window.mockServer.send(JSON.stringify(message));
                setTimeout(function () {
                    expect($(".grid-item:contains('adds new content')").length).to.eq(1);
                    expect($(".grid-item-bar > span:contains('2 minutes ago')").length).to.eq(1);
                    expect($(".grid-item-bar > span[title='2017-01-02 10:11:12+00:00']").length).to.eq(1);
                    done();
                }, 500);
            });

            after(function() {
                $("#new-content-count").html(0);
                $("#new-content-container").hide();
            });
        });
    });

    describe("nsfw", function() {
        context("shield", function() {
            it("activates", function() {
                var $nsfw = $("#nsfw-content");
                expect($nsfw.is(":visible")).to.be.false;
                expect($nsfw.hasClass("nsfw-shield-on")).to.be.true;
                var $card = $nsfw.prev();
                expect($card.is(":visible")).to.be.true;
            });

            it("shows image on shield click and hides it on returned click", function() {
                var $nsfw = $("#nsfw-content"),
                    $card = $nsfw.prev();
                $card.trigger("click");
                expect($nsfw.is(":visible")).to.be.true;
                expect($nsfw.hasClass("nsfw-shield-off")).to.be.true;
                var $returner = $nsfw.prev();
                expect($returner.is(":visible")).to.be.true;
                $returner.trigger("click");
                expect($nsfw.is(":visible")).to.be.false;
                expect($nsfw.hasClass("nsfw-shield-on")).to.be.true;
            });
        });
    });

    describe("modal", function() {
        before(function() {
            server = sinon.fakeServer.create();
            var data = {
                guid: "1234", rendered: "foobar", author_name: "sinon", author_handle: "mocha@stream_test",
                author_image: "https://localhost/sinon.jpg",
            };
            server.respondWith(
                "GET",
                "/content/1234",
                [200, { "Content-Type": "application/json" }, JSON.stringify(data)]
            );
        });

        context("click on timestamp", function() {
            it("opens up modal", function() {
                var $modal = $(".modal-content");
                expect($modal.is(":visible")).to.be.false;
                $(".grid-item-open-action[data-content-guid=1234]").trigger("click", function(done) {
                    done();
                });
                server.respond();
                expect($modal.is(":visible")).to.be.true;
                expect($("#content-modal-title:contains('sinon')").length).to.eq(1);
                expect($("#content-modal-title:contains('mocha@stream_test')").length).to.eq(1);
                expect($("#content-modal-body:contains('foobar')").length).to.eq(1);
                expect($("#content-modal-profile-pic[src='https://localhost/sinon.jpg']").length).to.eq(1);
            });
        });

        after(function() {
            server.restore();
            $("#content-modal").modal("hide");
        });
    });
});
