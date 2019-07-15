import Vue from "vue"
import Moxios from "moxios"
import publisher from "@/store/modules/publisher"


describe("streamStore", () => {
    afterEach(() => {
        Sinon.restore()
        Moxios.install(Vue.prototype.$http)
    })

    afterEach(() => {
        Moxios.uninstall()
    })

    describe("publishPost", () => {
        it("should publish the post", done => {
            publisher.actions.publishPost({}, {
                pinned: true,
                text: "# This is a text",
                visibility: 0,
            })

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/content/")
                JSON.parse(request.config.data).should.eql({
                    order: 0,
                    parent: null,
                    pinned: true,
                    service_label: "",
                    text: "# This is a text",
                    visibility: 0,
                })
                done()
            })
        })
    })
})
