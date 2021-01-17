import {shallowMount, createLocalVue} from "@vue/test-utils"

import Vuex from "vuex"
import BootstrapVue from "bootstrap-vue"
import {VueMasonryPlugin} from "vue-masonry"

import NsfwShield from "@/components/streams/NsfwShield.vue"
import {getStore} from "%fixtures/store.fixtures"

const localVue = createLocalVue()
localVue.use(BootstrapVue)
localVue.use(VueMasonryPlugin)
localVue.use(Vuex)

describe("NsfwShield", () => {
    let store

    beforeEach(() => {
        Sinon.restore()
        store = getStore()
    })

    describe("lifecycle", () => {
        context("updated", () => {
            it("redraws masonry if not single stream", () => {
                store.state.stream.stream.single = false
                const target = shallowMount(NsfwShield, {
                    propsData: {tags: ["nsfw"]}, store, localVue,
                })
                Sinon.spy(target.vm, "$redrawVueMasonry")
                target.vm.$forceUpdate()
                target.vm.$redrawVueMasonry.called.should.be.true
            })

            it("does not redraw masonry if single stream", () => {
                store.state.stream.stream.single = true
                const target = shallowMount(NsfwShield, {
                    propsData: {tags: ["nsfw"]}, store, localVue,
                })
                Sinon.spy(target.vm, "$redrawVueMasonry")
                target.vm.$forceUpdate()
                target.vm.$redrawVueMasonry.called.should.be.false
            })
        })
    })

    describe("methods", () => {
        describe("onImageLoad", () => {
            context("call Vue.redrawVueMasonry", () => {
                it("does if not single stream", () => {
                    const target = shallowMount(NsfwShield, {
                        propsData: {tags: ["nsfw"]}, store, localVue,
                    })
                    Sinon.spy(target.vm, "$redrawVueMasonry")
                    target.vm.onImageLoad()
                    target.vm.$redrawVueMasonry.called.should.be.true
                })

                it("does not if single stream", () => {
                    store.state.stream.stream.single = true
                    const target = shallowMount(NsfwShield, {
                        propsData: {tags: ["nsfw"]}, store, localVue,
                    })
                    Sinon.spy(target.vm, "$redrawVueMasonry")
                    target.vm.onImageLoad()
                    target.vm.$redrawVueMasonry.called.should.be.false
                })
            })
        })

        describe("toggleNsfwShield", () => {
            it("should toggle `showNsfwContent`", () => {
                const target = shallowMount(NsfwShield, {
                    propsData: {tags: ["nsfw"]}, store, localVue,
                })
                target.vm.showNsfwContent.should.be.false
                target.vm.toggleNsfwShield()
                target.vm.showNsfwContent.should.be.true
                target.vm.toggleNsfwShield()
                target.vm.showNsfwContent.should.be.false
            })

            it("should show and hide content", done => {
                const target = shallowMount(NsfwShield, {
                    propsData: {tags: ["nsfw"]},
                    slots: {default: {template: "<div>This is #NSFW content</div>"}},
                    store,
                    localVue,
                })

                target.text().should.not.match(/This is #NSFW content/)
                target.vm.toggleNsfwShield()
                target.vm.$nextTick().then(() => {
                    target.text().should.match(/This is #NSFW content/)
                    done()
                }).catch(done)
            })
        })
    })
})
