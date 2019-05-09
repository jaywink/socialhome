import Vue from "vue"
import Moxios from "moxios"
import Axios from "axios"
import publisher from "frontend/store/modules/publisher"

describe("streamStore", () => {
    afterEach(() => {
        Sinon.restore()
        Vue.prototype.$http = Axios.create({
            xsrfCookieName: "csrftoken",
            xsrfHeaderName: "X-CSRFToken",
        })
        Moxios.install(Vue.prototype.$http)
    })

    afterEach(() => {
        Moxios.uninstall()
    })

    describe("publishPost", function () {
        it("should publish the post", (done) => {
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
