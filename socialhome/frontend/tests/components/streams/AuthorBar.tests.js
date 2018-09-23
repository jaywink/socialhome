import BootstrapVue from "bootstrap-vue"
import Vue from "vue"
import VueMasonryPlugin from "vue-masonry"
import {mount} from "avoriaz"

import AuthorBar from "frontend/components/streams/AuthorBar.vue"
import {getContext, getFakeContent, getFakeAuthor} from "frontend/tests/fixtures/jsonContext.fixtures"
import {newApplicationStore} from "frontend/stores/applicationStore"
import {newStreamStore} from "frontend/stores/streamStore"


Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)

describe("AuthorBar", () => {
    let content
    let store

    beforeEach(() => {
        Sinon.restore()

        content = getFakeContent({
            id: 1,
            author: getFakeAuthor({uuid: "42"}),
        })
        window.context = getContext({currentBrowsingProfileId: 26}, 0)
        store = newStreamStore({modules: {applicationStore: newApplicationStore()}})
        store.state.contentIds.push(content.id)
        Vue.set(store.state.contents, content.id, content)
    })

    describe("methods", () => {
        beforeEach(() => {
            Sinon.restore()
        })

        describe("profileBoxTrigger", () => {
            it("should hide profilebox by default", () => {
                const target = mount(AuthorBar, {propsData: {content}, store})
                target.instance().showProfileBox.should.be.false
                target.find(".profile-box")[0].hasStyle("display", "none").should.be.true
            })

            it("should show profilebox when the author's name is clicked", () => {
                const target = mount(AuthorBar, {propsData: {content}, store})
                Sinon.spy(target.instance(), "profileBoxTrigger")
                target.find(".profilebox-trigger")[0].trigger("click")
                target.instance().profileBoxTrigger.calledOnce.should.be.true
                target.instance().showProfileBox.should.be.true
                target.find(".profile-box")[0].hasAttribute("display").should.be.false
            })
        })
    })

    describe("lifecycle", () => {
        describe("updated", () => {
            it("should redraw VueMasonry", done => {
                const target = mount(AuthorBar, {propsData: {content}, store})
                Sinon.spy(Vue, "redrawVueMasonry")
                target.update()
                target.vm.$nextTick(() => {
                    Vue.redrawVueMasonry.called.should.be.true
                    done()
                })
            })
        })
    })
})
