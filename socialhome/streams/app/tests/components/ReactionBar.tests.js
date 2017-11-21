import Axios from "axios"
import Moxios from "moxios"
import Vue from "vue"
import {mount} from "avoriaz"

import BootstrapVue from "bootstrap-vue"
import VueMasonryPlugin from "vue-masonry"

import ReactionsBar from "streams/app/components/ReactionsBar.vue"
import {getContext, getFakeContent} from "streams/app/tests/fixtures/jsonContext.fixtures"
import {newStreamStore} from "streams/app/stores/streamStore"
import applicationStore from "streams/app/stores/applicationStore"


Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)

describe("ReactionBar", () => {
    let content
    let store

    beforeEach(() => {
        Sinon.restore()

        content = getFakeContent({id: 1})
        window.context = getContext()
        store = newStreamStore({modules: {applicationStore}})
        store.state.contentIds.push(content.id)
        Vue.set(store.state.contents, content.id, content)
        return store
    })

    describe("computed", () => {
        describe("showReplies", () => {
            it("should be true if user is authenticated or content has replies", () => {
                let target = mount(ReactionsBar, {
                    propsData: {content},
                    store,
                })

                target.instance().$store.state.contents[1].reply_count = 0
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().showReplies.should.be.true

                target.instance().$store.state.contents[1].reply_count = 1
                target.instance().$store.state.applicationStore.isUserAuthenticated = false
                target.instance().showReplies.should.be.true

                target.instance().$store.state.contents[1].reply_count = 0
                target.instance().$store.state.applicationStore.isUserAuthenticated = false
                target.instance().showReplies.should.be.false
            })
        })

        describe("showShares", () => {
            it("should be true if user is authenticated or content has shares", () => {
                let target = mount(ReactionsBar, {
                    propsData: {content},
                    store,
                })

                target.instance().$store.state.contents[1].shares_count = 0
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().showShares.should.be.true

                target.instance().$store.state.contents[1].shares_count = 1
                target.instance().$store.state.applicationStore.isUserAuthenticated = false
                target.instance().showShares.should.be.true

                target.instance().$store.state.contents[1].shares_count = 0
                target.instance().$store.state.applicationStore.isUserAuthenticated = false
                target.instance().showShares.should.be.false
            })
        })
    })

    describe("methods", () => {
        beforeEach(() => {
            Vue.prototype.$http = Axios.create({
                xsrfCookieName: "csrftoken",
                xsrfHeaderName: "X-CSRFToken",
            })
            Moxios.install(Vue.prototype.$http)
        })

        afterEach(() => {
            Moxios.uninstall()
        })

        describe("expandShares", () => {
            it("should toggle showSharesBox", () => {
                let target = new ReactionsBar({propsData: {content}})
                target.expandShares()
                target.showSharesBox.should.be.true
                target.expandShares()
                target.showSharesBox.should.be.false
            })
        })

        describe("share", () => {
            it("should show the reshare box", () => {
                let target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().$store.state.contents[1].isUserAuthor = false
                target.instance().$data.showRepliesBox = true

                target.instance().expandShares()
                target.instance().$data.showSharesBox.should.be.true
            })

            it("should create share on server", (done) => {
                let target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().$store.state.contents[1].user_has_shared = false
                target.instance().$store.state.contents[1].user_is_author = false

                // Ensure data
                target.instance().expandShares()
                target.instance().showSharesBox.should.be.true
                target.instance().$store.state.contents[1].user_has_shared.should.be.false
                target.instance().$store.state.contents[1].shares_count = 12

                target.instance().share()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({
                        status: 200,
                        response: {status: "ok", content_id: 123},
                    }).then(() => {
                        target.instance().$data.showSharesBox.should.be.false
                        target.instance().$store.state.contents[1].user_has_shared.should.be.true
                        target.instance().$store.state.contents[1].shares_count.should.eq(13)
                        done()
                    })
                })
            })
        })

        describe("unshare", () => {
            it("should removes share on server", (done) => {
                let target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().$store.state.contents[1].user_has_shared = true
                target.instance().$store.state.contents[1].user_is_author = false

                // Ensure data
                target.instance().expandShares()
                target.instance().showSharesBox.should.be.true
                target.instance().$store.state.contents[1].user_has_shared.should.be.true
                target.instance().$store.state.contents[1].shares_count = 12

                // Actual thing we are testing - the unshare
                target.instance().unshare()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({
                        status: 200,
                        response: {status: "ok"},
                    }).then(() => {
                        target.instance().showSharesBox.should.be.false
                        target.instance().$store.state.contents[1].shares_count.should.eq(11)
                        target.instance().$store.state.contents[1].user_has_shared.should.be.false
                        done()
                    })
                })
            })
        })
    })
})
