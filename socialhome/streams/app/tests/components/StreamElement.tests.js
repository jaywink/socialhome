import {mount} from "avoriaz"
import infiniteScroll from "vue-infinite-scroll"
import Vue from "vue"
import VueMasonryPlugin from "vue-masonry"

import {getStore} from "streams/app/tests/fixtures/store.fixtures"
import {getFakeContent} from "streams/app/tests/fixtures/jsonContext.fixtures"
import {streamStoreOperations} from "streams/app/stores/streamStore.operations"
import StreamElement from "streams/app/components/StreamElement.vue"


Vue.use(infiniteScroll)
Vue.use(VueMasonryPlugin)

describe("StreamElement", () => {
    let store

    beforeEach(() => {
        store = getStore()
    })

    describe("computed", () => {
        it("disableLoadMore", () => {
            let content = getFakeContent({hasLoadMore: true})
            let target = mount(StreamElement, {propsData: {content}, store})
            target.instance().disableLoadMore.should.be.false

            target.instance().$store.state.pending.contents = true
            target.instance().disableLoadMore.should.be.true
            target.instance().$store.state.pending.contents = false

            content = getFakeContent({hasLoadMore: false})
            target = mount(StreamElement, {propsData: {content}, store})
            target.instance().disableLoadMore.should.be.true
        })

        it("showAuthorBar with content", () => {
            store.state.applicationStore.isUserAuthenticated = false
            let target = mount(StreamElement, {propsData: {content: store.content}, store})
            store.state.showAuthorBar = false
            target.instance().showAuthorBar.should.be.false
            store.state.showAuthorBar = true
            target.instance().showAuthorBar.should.be.true
            store.state.applicationStore.isUserAuthenticated = true
        })

        it("showAuthorBar with reply", () => {
            let target = mount(StreamElement, {propsData: {content: store.reply}, store})
            store.state.showAuthorBar = false
            target.instance().showAuthorBar.should.be.true
            store.state.showAuthorBar = true
            target.instance().showAuthorBar.should.be.true
        })

        it("showAuthorBar with other author", () => {
            let otherContent = Object.assign({}, store.content)
            otherContent.user_is_author = false
            let target = mount(StreamElement, {propsData: {content: otherContent}, store})
            store.state.showAuthorBar = false
            target.instance().showAuthorBar.should.be.true
        })
    })

    describe("methods", () => {
        it("loadMore dispatches stream operations", () => {
            let target = mount(StreamElement, {propsData: {content: store.content}, store})
            Sinon.spy(target.instance().$store, "dispatch")
            target.instance().loadMore()
            target.instance().$store.dispatch.getCall(0).args[0].should.eql(streamStoreOperations.disableLoadMore)
            target.instance().$store.dispatch.getCall(0).args[1].should.eql(store.content.id)
            target.instance().$store.dispatch.getCall(1).args[0].should.eql(streamStoreOperations.loadStream)
        })
    })

    describe("updated", () => {
        it("redraws masonry", done => {
            let target = mount(StreamElement, {propsData: {content: store.content}, store})
            Sinon.spy(Vue, "redrawVueMasonry")
            target.update()
            target.instance().$nextTick(() => {
            Vue.redrawVueMasonry.called.should.be.true
                done()
            })
        })
    })
})
