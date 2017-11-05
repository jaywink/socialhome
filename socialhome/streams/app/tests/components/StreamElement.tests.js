import {mount} from "avoriaz"
import Vue from "vue"
import VueMasonryPlugin from "vue-masonry"

import {getStore} from "streams/app/tests/fixtures/store.fixtures"
import StreamElement from "streams/app/components/StreamElement.vue"


Vue.use(VueMasonryPlugin)

describe("StreamElement", () => {
    let store

    beforeEach(() => {
        store = getStore()
    })

    describe("computer", () => {
        it("showAuthorBar with content", () => {
            let target = mount(StreamElement, {propsData: {contentId: store.content.id}, store})
            store.state.showAuthorBar = false
            target.instance().showAuthorBar.should.be.false
            store.state.showAuthorBar = true
            target.instance().showAuthorBar.should.be.true
        })

        it("showAuthorBar with reply", () => {
            let target = mount(StreamElement, {propsData: {contentId: store.reply.id}, store})
            store.state.showAuthorBar = false
            target.instance().showAuthorBar.should.be.true
            store.state.showAuthorBar = true
            target.instance().showAuthorBar.should.be.true
        })
    })

    describe("updated", () => {
        it("redraws masonry", done => {
            let target = mount(StreamElement, {propsData: {contentId: store.content.id}, store})
            Sinon.spy(Vue, "redrawVueMasonry")
            target.update()
            target.instance().$nextTick(() => {
            Vue.redrawVueMasonry.called.should.be.true
                done()
            })
        })
    })

    describe("mounted", () => {

    })
})
