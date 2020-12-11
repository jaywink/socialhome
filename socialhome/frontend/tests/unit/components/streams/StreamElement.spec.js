import {shallowMount, createLocalVue} from "@vue/test-utils"
import infiniteScroll from "vue-infinite-scroll"
import Vuex from "vuex"
import BootstrapVue from "bootstrap-vue"
import {VueMasonryPlugin} from "vue-masonry"

import StreamElement from "@/components/streams/StreamElement.vue"
import {getStore} from "%fixtures/store.fixtures"
import {getFakeContent} from "%fixtures/jsonContext.fixtures"

const localVue = createLocalVue()
localVue.use(BootstrapVue)
localVue.use(infiniteScroll)
localVue.use(VueMasonryPlugin)
localVue.use(Vuex)

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
            let target = shallowMount(StreamElement, {
                propsData: {content}, store, localVue,
            })
            target.vm.disableLoadMore.should.be.false

            store.state.stream.pending.contents = true
            target = shallowMount(StreamElement, {
                propsData: {content}, store, localVue,
            })
            target.vm.disableLoadMore.should.be.true
            store.state.stream.pending.contents = false

            content = getFakeContent({hasLoadMore: false})
            target = shallowMount(StreamElement, {
                propsData: {content}, store, localVue,
            })
            target.vm.disableLoadMore.should.be.true
        })

        it("showAuthorBar with content", () => {
            store.state.application.isUserAuthenticated = false
            store.state.stream.showAuthorBar = false
            let target = shallowMount(StreamElement, {
                propsData: {content: store.content}, store, localVue,
            })
            target.vm.showAuthorBar.should.be.false
            store.state.stream.showAuthorBar = true
            target = shallowMount(StreamElement, {
                propsData: {content: store.content}, store, localVue,
            })
            target.vm.showAuthorBar.should.be.true
            store.state.application.isUserAuthenticated = true
        })

        it("showAuthorBar with reply", () => {
            const target = shallowMount(StreamElement, {
                propsData: {content: store.reply}, store, localVue,
            })
            store.state.showAuthorBar = false
            target.vm.showAuthorBar.should.be.true
            store.state.showAuthorBar = true
            target.vm.showAuthorBar.should.be.true
        })

        it("showAuthorBar with other author", () => {
            const otherContent = {...store.content}
            otherContent.user_is_author = false
            const target = shallowMount(StreamElement, {
                propsData: {content: otherContent}, store, localVue,
            })
            store.state.showAuthorBar = false
            target.vm.showAuthorBar.should.be.true
        })
    })

    describe("methods", () => {
        it("loadMore dispatches stream operations", () => {
            const target = shallowMount(StreamElement, {
                propsData: {content: store.content}, store, localVue,
            })
            Sinon.spy(target.vm, "$emit")
            target.vm.loadMore()
            target.vm.$store.dispatch.should.have.been.calledWithExactly("stream/disableLoadMore", Sinon.match.number)
            target.vm.$emit.getCall(0).args[0].should.eql("loadmore")
        })
    })

    describe("lifecycle", () => {
        describe("updated", () => {
            it("redraws masonry", () => {
                const target = shallowMount(StreamElement, {
                    propsData: {content: store.content}, store, localVue,
                })
                Sinon.spy(target.vm, "$redrawVueMasonry")
                target.vm.$forceUpdate()
                target.vm.$redrawVueMasonry.should.have.been.called
            })
        })
    })
})
