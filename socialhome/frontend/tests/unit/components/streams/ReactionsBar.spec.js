import Vuex from "vuex"
import {createLocalVue, shallowMount} from "@vue/test-utils"
import BootstrapVue from "bootstrap-vue"
import VueSnotify from "vue-snotify"
import {VueMasonryPlugin} from "vue-masonry"

import ReactionsBar from "@/components/streams/ReactionsBar.vue"
import {getContext, getFakeContent} from "%fixtures/jsonContext.fixtures"
import {getStore} from "%fixtures/store.fixtures"

const localVue = createLocalVue()

localVue.use(BootstrapVue)
localVue.use(VueMasonryPlugin)
localVue.use(VueSnotify)
localVue.use(Vuex)

describe("ReactionsBar", () => {
    let content
    let store

    beforeEach(() => {
        Sinon.restore()

        content = getFakeContent({id: 1})
        window.context = getContext()
        store = getStore()
        store.state.stream.currentContentIds.push(content.id)
        localVue.set(store.state.stream.contents, content.id, content)
    })

    describe("computed", () => {
        describe("showExpandRepliesIcon", () => {
            it("should be true if content has replies", () => {
                store.state.stream.contents[content.id].reply_count = 0
                let target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showExpandRepliesIcon.should.be.false

                store.state.stream.contents[content.id].reply_count = 1
                target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showExpandRepliesIcon.should.be.true
            })
        })

        describe("showSharesCountIcon", () => {
            it("should be true if content has shares", () => {
                store.state.stream.contents[content.id].shares_count = 0
                let target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showSharesCountIcon.should.be.false

                store.state.stream.contents[content.id].shares_count = 1
                target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showSharesCountIcon.should.be.true
            })
        })
    })

    describe("lifecycle", () => {
        context("updated", () => {
            it("redraws masonry if not single stream", () => {
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                Sinon.spy(target.vm, "$redrawVueMasonry")
                target.vm.$forceUpdate()
                target.vm.$redrawVueMasonry.called.should.be.true
            })

            it("does not redraw masonry if single stream", () => {
                store.state.stream.stream.single = true
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                Sinon.spy(target.vm, "$redrawVueMasonry")
                target.vm.$forceUpdate()
                target.vm.$redrawVueMasonry.called.should.be.false
            })
        })
    })
})
