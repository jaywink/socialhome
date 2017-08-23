import {mount} from "avoriaz"

import Vue from "vue"
import BootstrapVue from "bootstrap-vue"

import Stream from "streams/app/components/Stream.vue"
import {store, stateOperations} from "streams/app/stores/streamStore"


Vue.use(BootstrapVue)

describe("Stream", () => {
    afterEach(() => {
        Sinon.restore()
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
                store.commit(stateOperations.receivedNewContent, 1)
                target.instance().$nextTick(() => {
                    target.find(".new-content-container")[0].hasStyle("display", "none").should.be.false
                    target.find(".new-content-container .badge")[0].text().should.match(/1 new posts available/)
                    done()
                })
            })

            it("should acknowledge new content when the user clicks the button", () => {
                let target = mount(Stream, {})
                store.commit(stateOperations.receivedNewContent, 1)
                Sinon.spy(store, "dispatch")
                target.find(".new-content-load-link")[0].trigger("click")
                store.dispatch.calledWith(stateOperations.newContentAck).should.be.true
            })
        })
    })
})
