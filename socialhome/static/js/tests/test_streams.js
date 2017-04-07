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
                        formatted_timestamp: "2017-01-02 10:11:12+00:00",
                        author_image: "http://localhost/foobar.png", author_name: "Some Author",
                    }]
                };
                window.mockServer.send(JSON.stringify(message));
                setTimeout(function () {
                    expect($(".grid-item:contains('adds new content')").length).to.eq(1);
                    expect($(".grid-item-bar > span:contains('2 minutes ago')").length).to.eq(1);
                    expect($(".grid-item-bar > span[title='2017-01-02 10:11:12+00:00']").length).to.eq(1);
                    expect($(".grid-item-author-bar-pic[src='http://localhost/foobar.png']").length).to.eq(1);
                    expect($(".grid-item-author-bar:contains('Some Author')").length).to.eq(1);
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
                id: 1, guid: "1234", rendered: "foobar barfoo", author_name: "sinon", author_handle: "mocha@stream_test",
                author_image: "https://localhost/sinon.jpg", slug: "foobar-barfoo",
                formatted_timestamp: "2017-03-14 22:04:00+00:00", humanized_timestamp: "2 hours ago",
                is_author: false, update_url: "", delete_url: "",
            };
            server.respondWith(
                "GET",
                "/content/1234/",
                [200, { "Content-Type": "application/json" }, JSON.stringify(data)]
            );
        });

        context("as author", function() {
            before(function() {
                server = sinon.fakeServer.create();
                var data = {
                    id: 1, guid: "1234", rendered: "foobar barfoo", author_name: "sinon", author_handle: "mocha@stream_test",
                    author_image: "https://localhost/sinon.jpg", slug: "foobar-barfoo",
                    formatted_timestamp: "2017-03-14 22:04:00+00:00", humanized_timestamp: "2 hours ago",
                    is_author: true, update_url: "http://127.0.0.1:" + runserverPort + "/content/1/~update/",
                    delete_url: "http://127.0.0.1:" + runserverPort + "/content/1/~delete/",
                };
                server.respondWith(
                    "GET",
                    "/content/1234/",
                    [200, { "Content-Type": "application/json" }, JSON.stringify(data)]
                );
            });

            it("click on timestamp opens up modal", function() {
                var $modal = $(".modal-content");
                expect($modal.is(":visible")).to.be.false;
                $(".grid-item-open-action[data-content-guid=1234]").trigger("click", function(done) {
                    done();
                });
                server.respond();
                expect($("#content-bar-actions").hasClass("hidden")).to.be.false;
                expect($("#content-update-link").attr("href")).to.eq("http://127.0.0.1:" + runserverPort + "/content/1/~update/");
                expect($("#content-delete-link").attr("href")).to.eq("http://127.0.0.1:" + runserverPort + "/content/1/~delete/");
            });

            after(function() {
                server.restore();
            });
        });

        it("changes url to content and then back on hiding modal", function() {
            var currentUrl = window.location.href;
            expect(currentUrl).to.not.eq("http://127.0.0.1:" + runserverPort + "/content/1/foobar-barfoo/");
            $(".grid-item-open-action[data-content-guid=1234]").trigger("click", function(done) {
                done();
            });
            server.respond();
            expect(window.location.href).to.eq("http://127.0.0.1:" + runserverPort + "/content/1/foobar-barfoo/");
            $("#content-modal").modal("hide");
            setTimeout(function() {
                expect(window.location.href).to.eq(currentUrl);
            }, 100);
        });

        it("hides modal on back navigation", function() {
            var $modal = $(".modal-content");
            $(".grid-item-open-action[data-content-guid=1234]").trigger("click", function(done) {
                done();
            });
            server.respond();
            expect($modal.is(":visible")).to.be.true;
            history.back();
            setTimeout(function() {
                expect($modal.is(":visible")).to.be.false;
            }, 100);
        });

        it("click on timestamp opens up modal", function() {
            var $modal = $(".modal-content");
            expect($modal.is(":visible")).to.be.false;
            $(".grid-item-open-action[data-content-guid=1234]").trigger("click", function(done) {
                done();
            });
            server.respond();
            expect($modal.is(":visible")).to.be.true;
            expect($("#content-title:contains('sinon')").length).to.eq(1);
            expect($("#content-title:contains('mocha@stream_test')").length).to.eq(1);
            expect($("#content-body:contains('foobar barfoo')").length).to.eq(1);
            expect($("#content-profile-pic[src='https://localhost/sinon.jpg']").length).to.eq(1);
            expect($("#content-timestamp[title='2017-03-14 22:04:00+00:00']").length).to.eq(1);
            expect($("#content-timestamp:contains('2 hours ago')").length).to.eq(1);
            expect($("#content-bar-actions").hasClass("hidden")).to.be.true;
            expect($("#content-update-link").attr("href")).to.eq("");
            expect($("#content-delete-link").attr("href")).to.eq("");
        });

        afterEach(function(done) {
            $("#content-modal").modal("hide");
            done();
        });

        after(function() {
            server.restore();
        });
    });
});
