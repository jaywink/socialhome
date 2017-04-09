$(function () {
    /*
     * Handle stream updates
     *
     * Connect to backend via a websocket. Listen to new content for the current stream.
     * Push new content to the view when user requests it.
     *
     */
    var view = {
        contentIds: [],

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
            var data = {
                content: content,
                stream: socialhomeStream.split("__")[0],
                objType: (content.parent) ? "comment" : "post",
            };
            var elem = Content.template(data);
            return $(elem);
        },

        addContentToGrid: function($contents, placement, parent_id) {
            if (placement === "appended") {
                $('.grid').append($contents).masonry(placement, $contents, true);
            } else if (placement === "prepended") {
                $('.grid').prepend($contents).masonry(placement, $contents, true);
            } else if (placement === "children") {
                $(".grid-item[data-content-id='" + parent_id + "']").append($contents);
            }
            view.layoutMasonry();
            view.addNSFWShield();
        },

        layoutMasonry: function() {
            var $grid = $('.grid');
            $grid.imagesLoaded().progress(function (instance) {
                // Layout after every 5th image has loaded or at the end
                // Just a small performance tweak to not layout too often which becomes a problem
                // when loading infinitescroll items
                if (instance.progressedCount === instance.images.length ||
                        instance.progressedCount % 5 === 0) {
                    $grid.masonry('layout');
                }
            });
        },

        scrollToTop: function() {
            window.scrollTo(0, 0);
        },

        addNSFWShield: function() {
            // Add a clickable card element above the hidden image to show it
            $(".nsfw:not('.nsfw-shield-on')").each(function() {
              $(this).addClass("nsfw-shield-on").before(
                  $('<div class="card card-block text-xs-center nsfw-shield">' +
                      '<p class="card-text">[' + gettext("show NSFW image") + ']</p></div>')
              );
            });
            $(".nsfw-shield").off("click").click(view.showNSFWImage);
        },

        addNSFWShieldReturn: function() {
            // Add a clickable text above the visible image to reactivate the shield again
            $(".nsfw-shield-off:not('.nsfw-shield-off-active')").each(function() {
                $(this).addClass("nsfw-shield-off-active").before(
                    $('<div class="nsfw-shield-return">[' + gettext("hide NSFW image") + ']</div>')
                )
            });
            $(".nsfw-shield-return").off("click").click(view.returnNSFWShield);
        },

        showNSFWImage: function(ev) {
            // Make NSFW image visible
            var $elem = $(ev.currentTarget);
            $elem.hide().closest(".nsfw-shield").next().removeClass("nsfw nsfw-shield-on").addClass("nsfw-shield-off");
            view.addNSFWShieldReturn();
            view.layoutMasonry();
            $elem.remove();
        },

        returnNSFWShield: function(ev) {
            // Make NSFW image shielded again
            var $elem = $(ev.currentTarget);
            $elem.hide().next().addClass("nsfw").removeClass("nsfw-shield-off nsfw-shield-off-active");
            view.addNSFWShield();
            view.layoutMasonry();
            $elem.remove();
        },

        showContentModal: function() {
            $('#content-modal').modal('show').on('hide.bs.modal', function (e) {
                $('#content-modal').off("hide.bs.modal");
                history.back();
            });
            // Close modal on esc key
            $(document).keypress(function (ev) {
                if (ev.keyCode === 27) {
                    view.hideContentModal();
                }
            });
        },

        hideContentModal: function() {
            $('#content-modal').modal('hide');
        },

        cleanContentModal: function() {
            $('#content-title, #content-body').html("");
            $("#content-profile-pic").attr("src", "");
            $("#content-timestamp").attr("title", "").html("");
            $("#content-bar-actions").addClass("hidden");
            $("#content-update-link, #content-delete-link").attr("href", "");
        },

        setContentModalData: function(data) {
            // Add content to the modal
            $("#content-title").html(data.author_name + " &lt;" + data.author_handle + "&gt;");
            $("#content-body").html(data.rendered);
            $("#content-profile-pic").attr("src", data.author_image);
            $("#content-timestamp").attr("title", data.formatted_timestamp).html(data.humanized_timestamp);
            if (data.is_author) {
                $("#content-bar-actions").removeClass("hidden");
                $("#content-update-link").attr("href", data.update_url);
                $("#content-delete-link").attr("href", data.delete_url);
            }
        },

        loadContentModal: function(contentGuid) {
            $.getJSON(
                "/content/" + contentGuid + "/",
                function(data) {
                    // Change URL to the content URL
                    var url = "/content/" + data.id + "/";
                    if (data.slug !== "") {
                        url = url + data.slug + "/"
                    }
                    window.history.pushState(
                        {content: data.guid}, data.guid, url
                    );
                    view.setContentModalData(data);
                    view.addNSFWShield();
                }
            );
        },

        initContentIds: function() {
            $(".grid-item").each(function() {
                view.contentIds.push($(this).data("content-id"));
            });
        },

        getSmallestContentId: function() {
            return Math.min.apply(Math, view.contentIds);
        },
    };

    var controller = {
        availableContent: [],
        loadMoreTracker: undefined,

        init: function() {
            view.initContentIds();
            this.addContentListeners();
            this.addCommentTriggers();
            view.addNSFWShield();
            this.socket = this.createConnection();
            this.socket.onmessage = this.handleMessage;
            this.socket.onopen = this.handleSocketOpen;
            this.socket.onclose = this.handleSocketClose;
            // Hide content modal on back navigation
            window.onpopstate = function(ev) {
                $('#content-modal').off("hide.bs.modal");
                view.hideContentModal();
            };
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
            controller.addLoadMoreTrigger();
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
                    var $elem = view.createContentElem(content);
                    $contents = $contents ? $contents.add($elem) : $elem;
                    ids.push(content.id);
                });

                controller.availableContent = _.difference(controller.availableContent, ids);
                if (! controller.availableContent.length) {
                    view.hideNewLabel();
                }
                view.updateNewLabelCount(controller.availableContent.length);
                view.addContentToGrid($contents, data.placement, data.parent_id);
                view.contentIds = _.union(view.contentIds, ids);
                controller.addContentListeners();
                controller.addCommentTriggers();
                if (ids.length && data.placement === "appended") {
                    setTimeout(controller.addLoadMoreTrigger, 500);
                }
            }
        },

        addLoadMoreTrigger: function() {
            controller.loadMoreTracker = appear({
                elements: function elements(){
                    return $(".grid .grid-item:nth-last-child(5)");
                },
                appear: function appear(el) {
                    controller.loadMoreContent();
                },
                debounce: 200,
            });
        },

        getContent: function() {
            var data = {
                "action": "load_content",
                "ids": controller.availableContent
            };
            controller.socket.send(JSON.stringify(data));
            view.scrollToTop();
        },

        loadMoreContent: function() {
            if (controller.loadMoreTracker !== undefined) {
                controller.loadMoreTracker.destroy();
            }
            var data = {
                action: "load_more",
                last_id: view.getSmallestContentId(),
            };
            try {
                controller.socket.send(JSON.stringify(data));
            } catch(e) {
                console.log(e);
            }
        },

        loadContentModal: function(ev) {
            var contentGuid = $(ev.currentTarget).data("content-guid");
            view.cleanContentModal();
            view.showContentModal();
            view.loadContentModal(contentGuid);
        },

        openComments: function(ev) {
            var contentId = $(ev.currentTarget).data("content-id");
            var data = {
                action: "load_children",
                content_id: contentId,
            };
            try {
                controller.socket.send(JSON.stringify(data));
                $(ev.currentTarget).removeClass("item-open-comments-action").off("click");
            } catch(e) {
                console.log(e);
            }
        },

        addContentListeners: function() {
            $(".grid-item-open-action").off("click").click(this.loadContentModal);
        },

        addCommentTriggers: function() {
            $(".item-open-comments-action").off("click").click(this.openComments);
        },
    };

    if (typeof socialhomeStream !== "undefined") {
        controller.init();
    }
});
