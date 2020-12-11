import BootstrapVue from "bootstrap-vue"
import Vue from "vue"
import {VueMasonryPlugin} from "vue-masonry"
import {mount} from "avoriaz"

import AuthorBar from "@/components/streams/AuthorBar.vue"
import {getContext, getFakeContent, getFakeAuthor} from "%fixtures/jsonContext.fixtures"
import {getStore} from "%fixtures/store.fixtures"

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
        store = getStore()
        store.state.stream.currentContentIds.push(content.id)
        Vue.set(store.state.stream.contents, content.id, content)
    })

    describe("lifecycle", () => {
        describe("updated", () => {
            it("should redraw VueMasonry", done => {
                const target = mount(AuthorBar, {
                    propsData: {content}, store,
                })
                Sinon.spy(Vue.prototype, "$redrawVueMasonry")
                target.update()
                target.vm.$nextTick().then(() => {
                    Vue.prototype.$redrawVueMasonry.called.should.be.true
                    done()
                }).catch(done)
            })
        })
    })
})
