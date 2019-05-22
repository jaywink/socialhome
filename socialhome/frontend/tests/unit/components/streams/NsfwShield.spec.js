import {mount} from "avoriaz"

import Vue from "vue"
import Vuex from "vuex"
import BootstrapVue from "bootstrap-vue"
import {VueMasonryPlugin} from "vue-masonry"

import NsfwShield from "@/components/streams/NsfwShield.vue"
import {getStore} from "%fixtures/store.fixtures"

Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)
Vue.use(Vuex)


describe("NsfwShield", () => {
    let store

    beforeEach(() => {
        Sinon.restore()
        store = getStore()
    })

    describe("lifecycle", () => {
        context("updated", () => {
            it("redraws masonry if not single stream", done => {
                store.state.stream.stream.single = false
                const target = mount(NsfwShield, {propsData: {tags: ["nsfw"]}, store})
                Sinon.spy(Vue.prototype, "$redrawVueMasonry")
                target.update()
                target.vm.$nextTick().then(() => {
                    Vue.prototype.$redrawVueMasonry.called.should.be.true
                    done()
                }).catch(done)
            })

            it("does not redraw masonry if single stream", done => {
                store.state.stream.stream.single = true
                const target = mount(NsfwShield, {propsData: {tags: ["nsfw"]}, store})
                Sinon.spy(Vue.prototype, "$redrawVueMasonry")
                target.update()
                target.vm.$nextTick().then(() => {
                    Vue.prototype.$redrawVueMasonry.called.should.be.false
                    done()
                }).catch(done)
            })
        })
    })

    describe("methods", () => {
        describe("onImageLoad", () => {
            context("call Vue.redrawVueMasonry", () => {
                it("does if not single stream", () => {
                    const target = mount(NsfwShield, {propsData: {tags: ["nsfw"]}, store}).instance()
                    Sinon.spy(target, "$redrawVueMasonry")
                    target.onImageLoad()
                    target.$redrawVueMasonry.called.should.be.true
                })

                it("does not if single stream", () => {
                    store.state.stream.stream.single = true
                    const target = mount(NsfwShield, {propsData: {tags: ["nsfw"]}, store}).instance()
                    Sinon.spy(target, "$redrawVueMasonry")
                    target.onImageLoad()
                    target.$redrawVueMasonry.called.should.be.false
                })
            })
        })

        describe("toggleNsfwShield", () => {
            it("should toggle `showNsfwContent`", () => {
                const target = mount(NsfwShield, {propsData: {tags: ["nsfw"]}, store})
                target.instance().showNsfwContent.should.be.false
                target.instance().toggleNsfwShield()
                target.instance().showNsfwContent.should.be.true
                target.instance().toggleNsfwShield()
                target.instance().showNsfwContent.should.be.false
            })

            // TODO: Figure out the problem when works in the browser
            it.skip("should show and hide content", done => {
                const target = mount(NsfwShield, {
                    propsData: {tags: ["nsfw"]},
                    slots: {default: {template: "<div>This is #NSFW content</div>"}},
                    store,
                })

                target.text().should.not.match(/This is #NSFW content/)
                target.instance().toggleNsfwShield()
                target.instance().$nextTick().then(() => {
                    target.text().should.match(/This is #NSFW content/)
                    done()
                }).catch(done)
            })
        })
    })
})
