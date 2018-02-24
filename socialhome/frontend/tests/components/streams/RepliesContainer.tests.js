import {mount} from "avoriaz"
import Vue from "vue"
import BootstrapVue from "bootstrap-vue"
import VueMasonryPlugin from "vue-masonry"

import {getFakeContent} from "frontend/tests/fixtures/jsonContext.fixtures"
import {getStore} from "frontend/tests/fixtures/store.fixtures"
import {streamStoreOperations} from "frontend/stores/streamStore.operations"
import RepliesContainer from "frontend/components/streams/RepliesContainer.vue"

Vue.use(BootstrapVue)
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

        it("shares", () => {
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            target.instance().shares.should.eql([store.share])
        })

        context("showReplyButton", () => {
            it("shows reply button on root content", () => {
                let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
                target.instance().showReplyButton.should.be.true
            })

            it("does not show reply button for a share without replies", () => {
                store.share2 = getFakeContent({share_of: store.content.id, content_type: "share", reply_count: 0})
                Vue.set(store.state.shares, store.share2.id, store.share2)
                let target = mount(RepliesContainer, {propsData: {content: store.share2}, store})
                target.instance().showReplyButton.should.be.false
            })

            it("shows reply button for a share with replies", () => {
                store.share3 = getFakeContent({share_of: store.content.id, content_type: "share", reply_count: 1})
                Vue.set(store.state.shares, store.share3.id, store.share3)
                let target = mount(RepliesContainer, {propsData: {content: store.share3}, store})
                target.instance().showReplyButton.should.be.true
            })

            it("does not show reply button for a reply", () => {
                let target = mount(RepliesContainer, {propsData: {content: store.reply}, store})
                target.instance().showReplyButton.should.be.false
            })

            it("does not show reply button if reply editor is active", () => {
                let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
                target.instance().showReplyEditor()
                target.instance().showReplyButton.should.be.false
            })
        })
    })

    describe("methods", () => {
        describe("onImageLoad", () => {
            it("should call Vue.redrawVueMasonry if not single stream", () => {
                let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
                Sinon.spy(Vue, "redrawVueMasonry")
                target.instance().onImageLoad()
                Vue.redrawVueMasonry.called.should.be.true
            })

            it("should not call Vue.redrawVueMasonry if single stream", () => {
                store.state.stream.single = true
                let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
                Sinon.spy(Vue, "redrawVueMasonry")
                target.instance().onImageLoad()
                Vue.redrawVueMasonry.called.should.be.false
            })
        })

        describe("showReplyEditor", () => {
            it("toggles replyEditorActive", () => {
                let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
                target.instance().replyEditorActive.should.be.false
                target.instance().showReplyEditor()
                target.instance().replyEditorActive.should.be.true
            })
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
        it("redraws masonry if not single stream", done => {
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            Sinon.spy(Vue, "redrawVueMasonry")
            target.update()
            target.instance().$nextTick(() => {
            Vue.redrawVueMasonry.called.should.be.true
                done()
            })
        })

        it("does not redraw masonry if single stream", done => {
            store.state.stream.single = true
            let target = mount(RepliesContainer, {propsData: {content: store.content}, store})
            Sinon.spy(Vue, "redrawVueMasonry")
            target.update()
            target.instance().$nextTick(() => {
            Vue.redrawVueMasonry.called.should.be.false
                done()
            })
        })
    })
})
