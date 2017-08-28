describe("Content", function() {
    it("renders content grid-item if top level", function() {
        var tpl = Content.template({
            content: {
                parent: "",
            },
            stream: "foobar",
        });
        expect($(tpl).hasClass("grid-item")).to.be.true;
    });

    it("renders content reply if child level", function() {
        var tpl = Content.template({
            content: {
                parent: 4,
            },
            stream: "foobar",
        });
        expect($(tpl).hasClass("reply")).to.be.true;
    });

    it("renders author bar only for child or if not profile stream", function() {
        var tpl = Content.template({
            content: {
                parent: "",
            },
            stream: "profile",
        });
        expect($(tpl).find(".grid-item-author-bar").length).to.eql(0);
        tpl = Content.template({
            content: {
                parent: 3,
            },
            stream: "profile",
        });
        expect($(tpl).find(".grid-item-author-bar").length).to.eql(1);
        tpl = Content.template({
            content: {
                parent: "",
            },
            stream: "foobar",
        });
        expect($(tpl).find(".grid-item-author-bar").length).to.eql(1);
        tpl = Content.template({
            content: {
                parent: 5,
            },
            stream: "foobar",
        });
        expect($(tpl).find(".grid-item-author-bar").length).to.eql(1);
    });

    it("renders reply reactions if top level or (user authenticated or has replies)", function() {
        var tpl = Content.template({
            content: {
                parent: 2,
                is_authenticated: true,
                reply_count: 5,
            },
            stream: "foobar",
        });
        expect($(tpl).find(".item-open-replies-action").length).to.eql(0);
        tpl = Content.template({
            content: {
                parent: "",
                is_authenticated: false,
                reply_count: 0,
            },
            stream: "foobar",
        });
        expect($(tpl).find(".item-open-replies-action").length).to.eql(0);
        tpl = Content.template({
            content: {
                parent: "",
                is_authenticated: true,
                reply_count: 0,
            },
            stream: "foobar",
        });
        expect($(tpl).find(".item-open-replies-action").length).to.eql(1);
        tpl = Content.template({
            content: {
                parent: "",
                is_authenticated: false,
                reply_count: 1,
            },
            stream: "foobar",
        });
        expect($(tpl).find(".item-open-replies-action").length).to.eql(1);
    });
});
