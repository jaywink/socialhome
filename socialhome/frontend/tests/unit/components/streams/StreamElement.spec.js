import {mount} from "avoriaz"
import infiniteScroll from "vue-infinite-scroll"
import Vue from "vue"
import Vuex from "vuex"
import BootstrapVue from "bootstrap-vue"
import {VueMasonryPlugin} from "vue-masonry"

import {getStore} from "%fixtures/store.fixtures"
import {getFakeContent} from "%fixtures/jsonContext.fixtures"
import StreamElement from "@/components/streams/StreamElement.vue"

Vue.use(BootstrapVue)
Vue.use(infiniteScroll)
Vue.use(VueMasonryPlugin)
Vue.use(Vuex)

describe("StreamElement", () => {
    let store

    beforeEach(() => {
        store = getStore()
        Sinon.spy(store, "dispatch")
    })

    afterEach(() => {
        Sinon.restore()
    })

    describe("computed", () => {
        it("disableLoadMore", () => {
            let content = getFakeContent({hasLoadMore: true})
            let target = mount(StreamElement, {propsData: {content}, store})
            target.instance().disableLoadMore.should.be.false

            store.state.stream.pending.contents = true
            target = mount(StreamElement, {propsData: {content}, store})
            target.instance().disableLoadMore.should.be.true
            store.state.stream.pending.contents = false

            content = getFakeContent({hasLoadMore: false})
            target = mount(StreamElement, {propsData: {content}, store})
            target.instance().disableLoadMore.should.be.true
        })

        it("showAuthorBar with content", () => {
            store.state.application.isUserAuthenticated = false
            store.state.stream.showAuthorBar = false
            let target = mount(StreamElement, {propsData: {content: store.content}, store})
            target.instance().showAuthorBar.should.be.false
            store.state.stream.showAuthorBar = true
            target = mount(StreamElement, {propsData: {content: store.content}, store})
            target.instance().showAuthorBar.should.be.true
            store.state.application.isUserAuthenticated = true
        })

        it("showAuthorBar with reply", () => {
            const target = mount(StreamElement, {propsData: {content: store.reply}, store})
            store.state.showAuthorBar = false
            target.instance().showAuthorBar.should.be.true
            store.state.showAuthorBar = true
            target.instance().showAuthorBar.should.be.true
        })

        it("showAuthorBar with other author", () => {
            const otherContent = Object.assign({}, store.content)
            otherContent.user_is_author = false
            const target = mount(StreamElement, {propsData: {content: otherContent}, store})
            store.state.showAuthorBar = false
            target.instance().showAuthorBar.should.be.true
        })
    })

    describe("methods", () => {
        it("loadMore dispatches stream operations", () => {
            const target = mount(StreamElement, {propsData: {content: store.content}, store})
            Sinon.spy(target.instance(), "$emit")
            target.instance().loadMore()
            target.instance().$store.dispatch.getCall(0).args[0].should.eql("stream/disableLoadMore")
            target.instance().$emit.getCall(0).args[0].should.eql("loadmore")
        })
    })

    describe("lifecycle", () => {
        describe("updated", () => {
            it("redraws masonry", done => {
                store.state.stream.stream.single = false
                const target = mount(StreamElement, {propsData: {content: store.content}, store})
                Sinon.spy(target.instance(), "$redrawVueMasonry")
                target.update()
                target.instance().$nextTick().then(() => {
                    target.instance().$redrawVueMasonry.called.should.be.true
                    done()
                }).catch(done)
            })
        })
    })
})
