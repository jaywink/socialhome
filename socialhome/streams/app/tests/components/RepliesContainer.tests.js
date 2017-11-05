import {mount} from "avoriaz"
import Vue from "vue"
import VueMasonryPlugin from "vue-masonry"

import {getStore} from "streams/app/tests/fixtures/store.fixtures"
import {streamStoreOperations} from "streams/app/stores/streamStore.operations"
import RepliesContainer from "streams/app/components/RepliesContainer.vue"


Vue.use(VueMasonryPlugin)

describe("RepliesContainer", () => {
    let store

    beforeEach(() => {
        store = getStore()
        Sinon.stub(store, "dispatch")
    })

    afterEach(() => {
        Sinon.restore()
    })

    describe("computed", () => {
        it("isContent", () => {
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            target.instance().isContent.should.be.true

            target = mount(RepliesContainer, {propsData: {content: store.reply}, store})
            target.instance().isContent.should.be.false

            target = mount(RepliesContainer, {propsData: {content: store.share}, store})
            target.instance().isContent.should.be.false
        })

        it("isUserAuthenticated", () => {
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            target.instance().isUserAuthenticated.should.be.true
        })

        it("replies", () => {
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            target.instance().replies.should.eql([store.reply])
        })

        it("replyUrl", () => {
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            target.instance().replyUrl.should.eql(`/content/${store.content.id}/~reply/`)
        })

        it("shares", () => {
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            target.instance().shares.should.eql([store.share])
        })
    })

    describe("mounted", () => {
        it("dispatches getReplies and getShares on content", () => {
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            store.dispatch.callCount.should.eql(2)
            store.dispatch.args[0].should.eql([
                streamStoreOperations.getReplies, {params: {id: store.content.id}}
            ])
            store.dispatch.args[1].should.eql([
                streamStoreOperations.getShares, {params: {id: store.content.id}}
            ])
        })

        it("does not dispatch getReplies and getShares on share", () => {
            let target = mount(RepliesContainer, {propsData: {content: store.share}, store})
            store.dispatch.callCount.should.eql(0)
        })
    })

    describe("template", () => {
        it("contains replies", () => {
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            target.find(".reply").length.should.eql(2)
        })

        it("contains reply buttons if authenticated", () => {
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            target.html().indexOf("Reply").should.be.greaterThan(-1)
            target.html().indexOf("Reply to share").should.be.greaterThan(-1)

            store.state.applicationStore.isUserAuthenticated = false
            target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            target.html().indexOf("Reply").should.eql(-1)
            target.html().indexOf("Reply to share").should.eql(-1)
        })
    })

    describe("updated", () => {
        it("redraws masonry", done => {
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            Sinon.spy(Vue, "redrawVueMasonry")
            target.update()
            target.instance().$nextTick(() => {
            Vue.redrawVueMasonry.called.should.be.true
                done()
            })
        })
    })
})
