import {createLocalVue} from "@vue/test-utils"
import Moxios from "moxios"
import {getPublisherStore} from "@/store/modules/publisher"

const localVue = createLocalVue()
const publisher = getPublisherStore(localVue.axios)

describe("publisher", () => {
    beforeEach(() => {
        Sinon.restore()
        Moxios.install(localVue.prototype.$http)
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
                    federate: true,
                    include_following: false,
                    order: 0,
                    pinned: true,
                    recipients: "",
                    service_label: "",
                    show_preview: true,
                    text: "# This is a text",
                    visibility: 0,
                })
                done()
            })
        })
    })

    describe("publishReply", () => {
        it("should publish the post", done => {
            publisher.actions.publishReply({}, {
                parent: 24,
                text: "# This is a text",
            })

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/content/")
                JSON.parse(request.config.data).should.eql({
                    parent: 24,
                    show_preview: true,
                    text: "# This is a text",
                })
                done()
            })
        })
    })

    describe("editPost", () => {
        it("should publish the post", done => {
            publisher.actions.editPost({}, {
                contentId: 12,
                pinned: true,
                text: "# This is a text",
                visibility: 0,
            })

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/content/12/")
                JSON.parse(request.config.data).should.eql({
                    federate: true,
                    include_following: false,
                    order: 0,
                    pinned: true,
                    recipients: "",
                    service_label: "",
                    show_preview: true,
                    text: "# This is a text",
                    visibility: 0,
                })
                done()
            })
        })
    })

    describe("editReply", () => {
        it("should publish the post", done => {
            publisher.actions.editReply({}, {
                contentId: 12,
                parent: 24,
                text: "# This is a text",
            })

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/content/12/")
                JSON.parse(request.config.data).should.eql({
                    parent: 24,
                    show_preview: true,
                    text: "# This is a text",
                })
                done()
            })
        })
    })
})
