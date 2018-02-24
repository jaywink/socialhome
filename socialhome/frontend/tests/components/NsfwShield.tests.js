import {mount} from "avoriaz"

import Vue from "vue"
import BootstrapVue from "bootstrap-vue"
import VueMasonryPlugin from "vue-masonry"

import NsfwShield from "frontend/components/NsfwShield.vue"
import {getStore} from "frontend/tests/fixtures/store.fixtures"

Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)


describe("NsfwShield", () => {
    let store

    beforeEach(() => {
        Sinon.restore()
        store = getStore()
    })

    describe("lifecycle", () => {
        context("updated", () => {
            it("redraws masonry if not single stream", (done) => {
                let target = mount(NsfwShield, {propsData: {tags: ["nsfw"]}, store})
                Sinon.spy(Vue, "redrawVueMasonry")
                target.update()
                target.vm.$nextTick(() => {
                    Vue.redrawVueMasonry.called.should.be.true
                    done()
                })
            })

            it("does not redraw masonry if single stream", (done) => {
                store.state.stream.single = true
                let target = mount(NsfwShield, {propsData: {tags: ["nsfw"]}, store})
                Sinon.spy(Vue, "redrawVueMasonry")
                target.update()
                target.vm.$nextTick(() => {
                    Vue.redrawVueMasonry.called.should.be.false
                    done()
                })
            })
        })
    })

    describe("methods", () => {
        describe("onImageLoad", () => {
            context("call Vue.redrawVueMasonry", () => {
                it("does if not single stream", () => {
                    let target = mount(NsfwShield, {propsData: {tags: ["nsfw"]}, store})
                    Sinon.spy(Vue, "redrawVueMasonry")
                    target.instance().onImageLoad()
                    Vue.redrawVueMasonry.called.should.be.true
                })

                it("does not if single stream", () => {
                    store.state.stream.single = true
                    let target = mount(NsfwShield, {propsData: {tags: ["nsfw"]}, store})
                    Sinon.spy(Vue, "redrawVueMasonry")
                    target.instance().onImageLoad()
                    Vue.redrawVueMasonry.called.should.be.false
                })
            })
        })

        describe("toggleNsfwShield", () => {
            it("should toggle `showNsfwContent`", () => {
                let target = mount(NsfwShield, {propsData: {tags: ["nsfw"]}, store})
                target.instance().showNsfwContent.should.be.false
                target.instance().toggleNsfwShield()
                target.instance().showNsfwContent.should.be.true
                target.instance().toggleNsfwShield()
                target.instance().showNsfwContent.should.be.false
            })

            it("should show and hide content", (done) => {
                let target = mount(NsfwShield, {
                    propsData: {tags: ["nsfw"]},
                    slots: {"default": {template: "<div>This is #NSFW content</div>"}},
                    store,
                })

                target.text().should.not.match(/This is #NSFW content/)
                target.instance().toggleNsfwShield()
                target.instance().$nextTick(() => {
                    target.text().should.match(/This is #NSFW content/)
                    done()
                })
            })
        })
    })
})
