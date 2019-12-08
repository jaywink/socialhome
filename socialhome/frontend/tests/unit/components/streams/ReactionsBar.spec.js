import Moxios from "moxios"
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
        store.state.stream.contentIds.push(content.id)
        localVue.set(store.state.stream.contents, content.id, content)
    })

    describe("computed", () => {
        describe("showReplyReactionIcon", () => {
            it("should be true if user is authenticated or content has replies", () => {
                store.state.stream.contents[content.id].reply_count = 0
                store.state.application.isUserAuthenticated = true
                let target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showReplyReactionIcon.should.be.true

                store.state.stream.contents[content.id].reply_count = 1
                store.state.application.isUserAuthenticated = false
                target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showReplyReactionIcon.should.be.true

                store.state.stream.contents[content.id].reply_count = 0
                store.state.application.isUserAuthenticated = false
                target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showReplyReactionIcon.should.be.false
            })

            it("should be false if content is not of type content", () => {
                content.content_type = "reply"
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showReplyReactionIcon.should.be.false
            })
        })

        describe("showShareReactionIcon", () => {
            it("should be true if user is authenticated or content has shares", () => {
                store.state.stream.contents[content.id].shares_count = 0
                content.user_is_author = false
                store.state.application.isUserAuthenticated = true
                let target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showShareReactionIcon.should.be.true

                content.user_is_author = true
                target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showShareReactionIcon.should.be.false

                store.state.stream.contents[content.id].shares_count = 1
                store.state.application.isUserAuthenticated = false
                target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showShareReactionIcon.should.be.true

                store.state.stream.contents[content.id].shares_count = 0
                store.state.application.isUserAuthenticated = false
                target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showShareReactionIcon.should.be.false
            })

            it("should be false if content is not of type content", () => {
                content.content_type = "reply"
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.showShareReactionIcon.should.be.false
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

    describe("methods", () => {
        beforeEach(() => {
            Moxios.install(localVue.prototype.$http)
        })

        afterEach(() => {
            Moxios.uninstall()
        })

        describe("expandShares", () => {
            it("should toggle showSharesBox", () => {
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                target.vm.expandShares()
                target.vm.showSharesBox.should.be.true
                target.vm.expandShares()
                target.vm.showSharesBox.should.be.false
            })
        })

        describe("share", () => {
            it("should show the reshare box", () => {
                store.state.application.isUserAuthenticated = true
                store.state.stream.contents[content.id].isUserAuthor = false
                const target = shallowMount(ReactionsBar, {
                    propsData: {
                        content, showRepliesBox: true,
                    },
                    store,
                    localVue,
                })

                target.vm.expandShares()
                target.vm.$data.showSharesBox.should.be.true
            })

            it("should create share on server", done => {
                store.state.application.isUserAuthenticated = true
                store.state.stream.contents[content.id].user_has_shared = false
                store.state.stream.contents[content.id].user_is_author = false
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })

                // Ensure data
                target.vm.expandShares()
                target.vm.showSharesBox.should.be.true
                store.state.stream.contents[content.id].user_has_shared.should.be.false
                store.state.stream.contents[content.id].shares_count = 12

                target.vm.share()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({
                        status: 200,
                        response: {
                            status: "ok", content_id: 123,
                        },
                    }).then(() => {
                        target.vm.$data.showSharesBox.should.be.false
                        target.vm.$store.state.stream.contents[content.id].user_has_shared.should.be.true
                        target.vm.$store.state.stream.contents[content.id].shares_count.should.eq(13)
                        done()
                    })
                })
            })

            it("should show an error to the user when share fails", done => {
                store.state.application.isUserAuthenticated = true
                store.state.stream.contents[content.id].user_has_shared = false
                store.state.stream.contents[content.id].user_is_author = false
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                Sinon.spy(target.vm.$snotify, "error")

                target.vm.share()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 500}).then(() => {
                        target.vm.$snotify.error.should.have.been
                            .calledWithExactly("An error happened while resharing the content")
                        done()
                    })
                })
            })

            it("should show an error to the user when user is not logged in", () => {
                store.state.application.isUserAuthenticated = false
                store.state.stream.contents[content.id].user_has_shared = false
                store.state.stream.contents[content.id].user_is_author = false
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                Sinon.spy(target.vm.$snotify, "error")

                target.vm.share()

                target.vm.$snotify.error.should.have.been.calledWithExactly("You must be logged in to reshare")
            })

            it("should show an error to the user when user tries to share own post", () => {
                store.state.application.isUserAuthenticated = true
                store.state.stream.contents[content.id].user_has_shared = false
                store.state.stream.contents[content.id].user_is_author = true
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                Sinon.spy(target.vm.$snotify, "error")

                target.vm.share()

                target.vm.$snotify.error.should.have.been.calledWithExactly("Unable to reshare own post")
            })
        })

        describe("unshare", () => {
            it("should removes share on server", done => {
                store.state.application.isUserAuthenticated = true
                store.state.stream.contents[content.id].user_has_shared = true
                store.state.stream.contents[content.id].user_is_author = false
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })

                // Ensure data
                target.vm.expandShares()
                target.vm.showSharesBox.should.be.true
                target.vm.$store.state.stream.contents[content.id].user_has_shared.should.be.true
                target.vm.$store.state.stream.contents[content.id].shares_count = 12

                // Actual thing we are testing - the unshare
                target.vm.unshare()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({
                        status: 200,
                        response: {status: "ok"},
                    }).then(() => {
                        target.vm.showSharesBox.should.be.false
                        target.vm.$store.state.stream.contents[content.id].shares_count.should.eq(11)
                        target.vm.$store.state.stream.contents[content.id].user_has_shared.should.be.false
                        done()
                    })
                })
            })

            it("should show an error to the user when share fails", done => {
                store.state.application.isUserAuthenticated = true
                store.state.stream.contents[content.id].user_has_shared = false
                store.state.stream.contents[content.id].user_is_author = false
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                Sinon.spy(target.vm.$snotify, "error")

                target.vm.unshare()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 500}).then(() => {
                        target.vm.$snotify.error.should.have.been
                            .calledWithExactly("An error happened while unsharing the content")
                        done()
                    })
                })
            })

            it("should show an error to the user when user is not logged in", () => {
                store.state.application.isUserAuthenticated = false
                store.state.stream.contents[content.id].user_has_shared = false
                store.state.stream.contents[content.id].user_is_author = false
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                Sinon.spy(target.vm.$snotify, "error")

                target.vm.unshare()

                target.vm.$snotify.error.should.have.been.calledWithExactly("You must be logged in to unshare")
            })

            it("should show an error to the user when user tries to share own post", () => {
                store.state.application.isUserAuthenticated = true
                store.state.stream.contents[content.id].user_has_shared = false
                store.state.stream.contents[content.id].user_is_author = true
                const target = shallowMount(ReactionsBar, {
                    propsData: {content}, store, localVue,
                })
                Sinon.spy(target.vm.$snotify, "error")

                target.vm.unshare()

                target.vm.$snotify.error.should.have.been.calledWithExactly("Unable to unshare own post")
            })
        })
    })
})
