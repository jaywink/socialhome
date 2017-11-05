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
        it("isUserAuthenticated", () => {
            let target = mount(RepliesContainer, {propsData: {contentId: store.content.id}, store})
            target.instance().isUserAuthenticated.should.be.true
        })

        it("replies", () => {
            let target = mount(RepliesContainer, {propsData: {contentId: store.content.id}, store})
            target.instance().replies.should.eql([store.reply])
        })

        it("replyUrl", () => {
            let target = mount(RepliesContainer, {propsData: {contentId: store.content.id}, store})
            target.instance().replyUrl.should.eql(`/content/${store.content.id}/~reply/`)
        })

        it("shares", () => {
            let target = mount(RepliesContainer, {propsData: {contentId: store.content.id}, store})
            target.instance().shares.should.eql([store.share])
        })
    })

    describe("methods", () => {
        it("shareReplyUrl", () => {
            let target = mount(RepliesContainer, {propsData: {contentId: store.content.id}, store})
            target.instance().shareReplyUrl(store.share.id).should.eql(`/content/${store.share.id}/~reply/`)
        })
    })

    describe("mounted", () => {
        it("dispatches getReplies and getShares", () => {
            let target = mount(RepliesContainer, {propsData: {contentId: store.content.id}, store})
            store.dispatch.callCount.should.eql(2)
            store.dispatch.args[0].should.eql([
                streamStoreOperations.getReplies, {params: {id: store.content.id}}
            ])
            store.dispatch.args[1].should.eql([
                streamStoreOperations.getShares, {params: {id: store.content.id}}
            ])
        })
    })

    describe("template", () => {
        it("contains replies", () => {
            let target = mount(RepliesContainer, {propsData: {contentId: store.content.id}, store})
            target.find(".reply").length.should.eql(2)
        })

        it("contains reply buttons if authenticated", () => {
            let target = mount(RepliesContainer, {propsData: {contentId: store.content.id}, store})
            target.html().indexOf("Reply").should.be.greaterThan(-1)
            target.html().indexOf("Reply to share").should.be.greaterThan(-1)

            store.state.applicationStore.isUserAuthenticated = false
            target = mount(RepliesContainer, {propsData: {contentId: store.content.id}, store})
            target.html().indexOf("Reply").should.eql(-1)
            target.html().indexOf("Reply to share").should.eql(-1)
        })
    })
})
