import {mount} from "avoriaz"

import Vue from "vue"
import BootstrapVue from "bootstrap-vue"

import Stream from "streams/app/components/Stream.vue"
import PublicStampedElement from "streams/app/components/PublicStampedElement.vue"
import FollowedStampedElement from "streams/app/components/FollowedStampedElement.vue"
import {streamStoreOperations} from "streams/app/stores/streamStore"


Vue.use(BootstrapVue)

describe("Stream", () => {
    beforeEach(() => {
        Sinon.restore()
    })

    describe("computed", () => {
        describe("stampedElement", () => {
            it("should render the FollowedStampedElement when stream name is 'followed'", () => {
                let target = mount(Stream, {})
                target.instance().$store.state.streamName = "followed"
                target.instance().stampedElement.should.eq("FollowedStampedElement")
            })
            it("should render the PublicStampedElement when stream name is 'public'", () => {
                let target = mount(Stream, {})
                target.instance().$store.state.streamName = "public"
                target.instance().stampedElement.should.eq("PublicStampedElement")
            })
            it("should display an error when stream name is unknown", () => {
                let target = mount(Stream, {})
                Sinon.spy(console, "error")
                target.instance().$store.state.streamName = "Yolo stream"
                target.instance().stampedElement
                console.error.getCall(0).args[0].should.eq("Unsupported stream name Yolo stream")
            })
        })
    })

    describe("methods", () => {
        describe("onImageLoad", () => {
            it("should call Vue.redrawVueMasonry", () => {
                let target = new Stream({})
                Sinon.spy(Vue, "redrawVueMasonry")
                target.onImageLoad()
            })
        })
        describe("onNewContentClick", () => {
            it("should show the new content button when the user receives new content", (done) => {
                let target = mount(Stream, {})
                target.find(".new-content-container")[0].hasStyle("display", "none").should.be.true
                target.instance().$store.commit(streamStoreOperations.receivedNewContent, 1)
                target.instance().$nextTick(() => {
                    target.find(".new-content-container")[0].hasStyle("display", "none").should.be.false
                    target.find(".new-content-container .badge")[0].text().should.match(/1 new posts available/)
                    done()
                })
            })

            it("should acknowledge new content when the user clicks the button", () => {
                let target = mount(Stream, {})
                target.instance().$store.commit(streamStoreOperations.receivedNewContent, 1)
                Sinon.spy(target.instance().$store, "dispatch")
                target.find(".new-content-load-link")[0].trigger("click")
                target.instance().$store.dispatch.getCall(0).args[0].should.eql(streamStoreOperations.newContentAck)
            })
        })
    })

    describe("Lifecycle", () => {
        describe("render", () => {
            it("should not render unfetched content", () => {
                let target = mount(Stream, {})
                target.find(".grid-item").length.should.eq(0)
                target.instance().$store.commit(streamStoreOperations.receivedNewContent, 1)
                target.find(".grid-item").length.should.eq(0)
            })
        })
    })
})
