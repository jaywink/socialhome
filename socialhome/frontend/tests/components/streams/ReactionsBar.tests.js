import Axios from "axios"
import Moxios from "moxios"
import Vue from "vue"
import Vuex from "vuex"
import {mount} from "avoriaz"
import BootstrapVue from "bootstrap-vue"
import VueSnotify from "vue-snotify"
import VueMasonryPlugin from "vue-masonry"

import ReactionsBar from "frontend/components/streams/ReactionsBar.vue"
import {getContext, getFakeContent} from "frontend/tests/fixtures/jsonContext.fixtures"
import {getStore} from "../../fixtures/store.fixtures"

Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)
Vue.use(VueSnotify)
Vue.use(Vuex)

describe("ReactionsBar", () => {
    let content
    let store

    beforeEach(() => {
        Sinon.restore()

        content = getFakeContent({id: 1})
        window.context = getContext()
        store = getStore()
        store.state.stream.contentIds.push(content.id)
        Vue.set(store.state.stream.contents, content.id, content)
    })

    describe("computed", () => {
        describe("showReplyReactionIcon", () => {
            it("should be true if user is authenticated or content has replies", () => {
                let target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.stream.contents[1].reply_count = 0
                target.instance().$store.state.application.isUserAuthenticated = true
                target.instance().showReplyReactionIcon.should.be.true

                target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.stream.contents[1].reply_count = 1
                target.instance().$store.state.application.isUserAuthenticated = false
                target.instance().showReplyReactionIcon.should.be.true

                target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.stream.contents[1].reply_count = 0
                target.instance().$store.state.application.isUserAuthenticated = false
                target.instance().showReplyReactionIcon.should.be.false
            })

            it("should be false if content is not of type content", () => {
                content.content_type = "reply"
                const target = mount(ReactionsBar, {
                    propsData: {content},
                    store,
                })
                target.instance().showReplyReactionIcon.should.be.false
            })
        })

        describe("showShareReactionIcon", () => {
            it("should be true if user is authenticated or content has shares", () => {
                let target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.stream.contents[1].shares_count = 0
                target.instance().$store.state.application.isUserAuthenticated = true
                target.instance().showShareReactionIcon.should.be.true

                target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.stream.contents[1].shares_count = 1
                target.instance().$store.state.application.isUserAuthenticated = false
                target.instance().showShareReactionIcon.should.be.true

                target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.stream.contents[1].shares_count = 0
                target.instance().$store.state.application.isUserAuthenticated = false
                target.instance().showShareReactionIcon.should.be.false
            })

            it("should be false if content is not of type content", () => {
                content.content_type = "reply"
                const target = mount(ReactionsBar, {
                    propsData: {content},
                    store,
                })
                target.instance().showShareReactionIcon.should.be.false
            })
        })
    })

    describe("lifecycle", () => {
        context("updated", () => {
            it("redraws masonry if not single stream", done => {
                const target = mount(ReactionsBar, {propsData: {content}, store})
                Sinon.spy(Vue, "redrawVueMasonry")
                target.update()
                target.vm.$nextTick(() => {
                    Vue.redrawVueMasonry.called.should.be.true
                    done()
                })
            })

            it("does not redraw masonry if single stream", done => {
                store.state.stream.stream.single = true
                const target = mount(ReactionsBar, {propsData: {content}, store})
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
                const target = new ReactionsBar({propsData: {content}})
                target.expandShares()
                target.showSharesBox.should.be.true
                target.expandShares()
                target.showSharesBox.should.be.false
            })
        })

        describe("share", () => {
            it("should show the reshare box", () => {
                const target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.application.isUserAuthenticated = true
                target.instance().$store.state.stream.contents[1].isUserAuthor = false
                target.instance().$data.showRepliesBox = true

                target.instance().expandShares()
                target.instance().$data.showSharesBox.should.be.true
            })

            it("should create share on server", done => {
                const target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.application.isUserAuthenticated = true
                target.instance().$store.state.stream.contents[1].user_has_shared = false
                target.instance().$store.state.stream.contents[1].user_is_author = false

                // Ensure data
                target.instance().expandShares()
                target.instance().showSharesBox.should.be.true
                target.instance().$store.state.stream.contents[1].user_has_shared.should.be.false
                target.instance().$store.state.stream.contents[1].shares_count = 12

                target.instance().share()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({
                        status: 200,
                        response: {status: "ok", content_id: 123},
                    }).then(() => {
                        target.instance().$data.showSharesBox.should.be.false
                        target.instance().$store.state.stream.contents[1].user_has_shared.should.be.true
                        target.instance().$store.state.stream.contents[1].shares_count.should.eq(13)
                        done()
                    })
                })
            })

            it("should show an error to the user when share fails", done => {
                const target = mount(ReactionsBar, {propsData: {content}, store})
                Sinon.spy(target.instance().$snotify, "error")
                target.instance().$store.state.application.isUserAuthenticated = true
                target.instance().$store.state.stream.contents[1].user_has_shared = false
                target.instance().$store.state.stream.contents[1].user_is_author = false

                target.instance().share()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 500}).then(() => {
                        target.instance().$snotify.error.getCall(0).args[0]
                            .should.eq("An error happened while resharing the content")
                        done()
                    })
                })
            })

            it("should show an error to the user when user is not logged in", () => {
                const target = mount(ReactionsBar, {propsData: {content}, store})
                Sinon.spy(target.instance().$snotify, "error")
                target.instance().$store.state.application.isUserAuthenticated = false
                target.instance().$store.state.stream.contents[1].user_has_shared = false
                target.instance().$store.state.stream.contents[1].user_is_author = false

                target.instance().share()

                target.instance().$snotify.error.getCall(0).args[0]
                    .should.eq("You must be logged in to reshare")
            })

            it("should show an error to the user when user tries to share own post", () => {
                const target = mount(ReactionsBar, {propsData: {content}, store})
                Sinon.spy(target.instance().$snotify, "error")
                target.instance().$store.state.application.isUserAuthenticated = true
                target.instance().$store.state.stream.contents[1].user_has_shared = false
                target.instance().$store.state.stream.contents[1].user_is_author = true

                target.instance().share()

                target.instance().$snotify.error.getCall(0).args[0]
                    .should.eq("Unable to reshare own post")
            })
        })

        describe("unshare", () => {
            it("should removes share on server", done => {
                const target = mount(ReactionsBar, {propsData: {content}, store})
                target.instance().$store.state.application.isUserAuthenticated = true
                target.instance().$store.state.stream.contents[1].user_has_shared = true
                target.instance().$store.state.stream.contents[1].user_is_author = false

                // Ensure data
                target.instance().expandShares()
                target.instance().showSharesBox.should.be.true
                target.instance().$store.state.stream.contents[1].user_has_shared.should.be.true
                target.instance().$store.state.stream.contents[1].shares_count = 12

                // Actual thing we are testing - the unshare
                target.instance().unshare()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({
                        status: 200,
                        response: {status: "ok"},
                    }).then(() => {
                        target.instance().showSharesBox.should.be.false
                        target.instance().$store.state.stream.contents[1].shares_count.should.eq(11)
                        target.instance().$store.state.stream.contents[1].user_has_shared.should.be.false
                        done()
                    })
                })
            })

            it("should show an error to the user when share fails", done => {
                const target = mount(ReactionsBar, {propsData: {content}, store})
                Sinon.spy(target.instance().$snotify, "error")
                target.instance().$store.state.application.isUserAuthenticated = true
                target.instance().$store.state.stream.contents[1].user_has_shared = false
                target.instance().$store.state.stream.contents[1].user_is_author = false

                target.instance().unshare()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 500}).then(() => {
                        target.instance().$snotify.error.getCall(0).args[0]
                            .should.eq("An error happened while unsharing the content")
                        done()
                    })
                })
            })

            it("should show an error to the user when user is not logged in", () => {
                const target = mount(ReactionsBar, {propsData: {content}, store})
                Sinon.spy(target.instance().$snotify, "error")
                target.instance().$store.state.application.isUserAuthenticated = false
                target.instance().$store.state.stream.contents[1].user_has_shared = false
                target.instance().$store.state.stream.contents[1].user_is_author = false

                target.instance().unshare()

                target.instance().$snotify.error.getCall(0).args[0]
                    .should.eq("You must be logged in to unshare")
            })

            it("should show an error to the user when user tries to share own post", () => {
                const target = mount(ReactionsBar, {propsData: {content}, store})
                Sinon.spy(target.instance().$snotify, "error")
                target.instance().$store.state.application.isUserAuthenticated = true
                target.instance().$store.state.stream.contents[1].user_has_shared = false
                target.instance().$store.state.stream.contents[1].user_is_author = true

                target.instance().unshare()

                target.instance().$snotify.error.getCall(0).args[0]
                    .should.eq("Unable to unshare own post")
            })
        })
    })
})
