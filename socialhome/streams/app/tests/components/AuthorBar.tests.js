import {mount} from "avoriaz"
import Moxios from "moxios"

import Axios from "axios"
import BootstrapVue from "bootstrap-vue"
import Vue from "vue"
import VueMasonryPlugin from "vue-masonry"

import AuthorBar from "streams/app/components/AuthorBar.vue"
import {getContext, getFakeContent, getFakeAuthor} from "streams/app/tests/fixtures/jsonContext.fixtures"
import {newStreamStore} from "streams/app/stores/streamStore"
import {newApplicationStore} from "streams/app/stores/applicationStore"


Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)

describe("AuthorBar", () => {
    let store

    beforeEach(() => {
        Sinon.restore()

        let fakePost = getFakeContent({
            id: 1,
            author: getFakeAuthor({guid: "42"}),
        })
        window.context = getContext({currentBrowsingProfileId: 26}, 0)
        store = newStreamStore({modules: {applicationStore: newApplicationStore()}})
        store.state.contentIds.push(fakePost.id)
        Vue.set(store.state.contents, fakePost.id, fakePost)
    })

    describe("computed", () => {
        describe("isUserRemote", () => {
            it("should be the opposite of property isUserLocal", () => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.contents[1].author.is_local = true
                target.instance().isUserRemote.should.be.false

                target.instance().$store.state.contents[1].author.is_local = false
                target.instance().isUserRemote.should.be.true
            })
        })

        describe("canFollow", () => {
            it("should be true if user is authenticated and not the author", () => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.contents[1].user_is_author = true
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().canFollow.should.be.false

                target.instance().$store.state.contents[1].user_is_author = false
                target.instance().$store.state.applicationStore.isUserAuthenticated = false
                target.instance().canFollow.should.be.false

                target.instance().$store.state.contents[1].user_is_author = false
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().canFollow.should.be.true
            })
        })

        describe("showFollowBtn and showUnfollowBtn", () => {
            it("should show the follow button when the user can and is not following the author", (done) => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.contents[1].user_is_author = false
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().$store.state.contents[1].user_following_author = false

                target.instance().$nextTick(() => {
                    target.instance().showFollowBtn.should.be.true
                    target.instance().showUnfollowBtn.should.be.false
                    target.find(".follow-btn").length.should.equal(1)
                    done()
                })
            })

            it("should show the unfollow button when the user can and is not following the author", (done) => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.contents[1].user_is_author = false
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().$store.state.contents[1].user_following_author = true

                target.instance().$nextTick(() => {
                    target.instance().showFollowBtn.should.be.false
                    target.instance().showUnfollowBtn.should.be.true
                    target.find(".unfollow-btn").length.should.equal(1)
                    done()
                })
            })
        })

        describe("isUserFollowingAuthor", () => {
            it("should set value", () => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.contents[1].user_following_author = true
                target.instance().isUserFollowingAuthor.should.be.true
                target.instance().isUserFollowingAuthor = false
                target.instance().isUserFollowingAuthor.should.be.false
                target.instance().$store.state.contents[1].user_following_author.should.be.false
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

        describe("profileBoxTrigger", () => {
            it("should hide profilebox by default", () => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().showProfileBox.should.be.false
                target.find(".profile-box")[0].hasStyle("display", "none").should.be.true
            })

            it("should show profilebox when the author's name is clicked", () => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                Sinon.spy(target.instance(), "profileBoxTrigger")
                target.find(".profilebox-trigger")[0].trigger("click")
                target.instance().profileBoxTrigger.calledOnce.should.be.true
                target.instance().showProfileBox.should.be.true
                target.find(".profile-box")[0].hasAttribute("display", "none").should.be.false
            })
        })

        describe("unfollow", () => {
            it("should display an error message if the user is not logged in", () => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.applicationStore.isUserAuthenticated = false
                Sinon.spy(console, "error")
                target.instance().unfollow()
                console.error.calledWith("Not logged in").should.be.true
            })

            it("should not send an HTTP request if the user is not logged in", () => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.applicationStore.isUserAuthenticated = false
                Sinon.spy(target.instance().$http, "post")
                target.instance().unfollow()
                target.instance().$http.post.called.should.be.false
            })

            it("should send an HTTP request with the right parameters when user is logged in", () => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.applicationStore.isUserAuthenticated = true

                Sinon.spy(target.instance().$http, "post")
                target.instance().unfollow()
                target.instance().$http.post.getCall(0).args
                    .should.eql(["/api/profiles/26/remove_follower/", {guid: "42"}])
            })

            it("should show that user is following author when the HTTP request succeeds", (done) => {
                store.state.applicationStore.isUserAuthenticated = true
                store.state.contents[1].user_is_author = false
                store.state.contents[1].author.user_following_author = true
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})

                target.instance().unfollow()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 200}).then(() => {
                        target.vm.$nextTick(() => {
                            target.instance().isUserFollowingAuthor.should.be.false
                            target.find(".follow-btn").length.should.equal(1)
                            done()
                        })
                    })
                })
            })

            it("should show an error message when the HTTP request fails", (done) => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().$store.state.contents[1].user_is_author = false
                target.instance().$store.state.contents[1].author.user_following_author = true
                Sinon.spy(console, "error")

                target.instance().unfollow()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 500}).then(() => {
                        console.error.calledOnce.should.be.true
                        done()
                    })
                })
            })
        })

        describe("follow", () => {
            it("should display an error message if the user is not logged in", () => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.applicationStore.isUserAuthenticated = false
                Sinon.spy(console, "error")
                target.instance().follow()
                console.error.getCall(0).args[0].should.equal("Not logged in")
            })

            it("should not send an HTTP request if the user is not logged in", () => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.applicationStore.isUserAuthenticated = false
                Sinon.spy(target.instance().$http, "post")
                target.instance().follow()
                target.instance().$http.post.called.should.be.false
            })

            it("should send an HTTP request with the right parameters when user is logged in", () => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().$store.state.contents[1].user_is_author = false
                target.instance().$store.state.contents[1].author.user_following_author = false
                Sinon.spy(target.instance().$http, "post")
                target.instance().follow()
                target.instance().$http.post
                    .calledWith("/api/profiles/26/add_follower/", {guid: "42"}).should.be.true
            })

            it("should show that user is following author when the HTTP request succeeds", (done) => {
                store.state.applicationStore.isUserAuthenticated = true
                store.state.contents[1].user_is_author = false
                store.state.contents[1].author.user_following_author = false
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})

                target.instance().follow()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 200}).then(() => {
                        target.vm.$nextTick(() => {
                            target.instance().isUserFollowingAuthor.should.be.true
                            target.find(".unfollow-btn").length.should.equal(1)
                            done()
                        })
                    })
                })
            })

            it("should show an error message when the HTTP request fails", (done) => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
                target.instance().$store.state.applicationStore.isUserAuthenticated = true
                target.instance().$store.state.contents[1].user_is_author = false
                target.instance().$store.state.contents[1].author.user_following_author = false

                Sinon.spy(console, "error")
                target.instance().follow()

                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 500}).then(() => {
                        console.error.calledOnce.should.be.true
                        done()
                    })
                })
            })
        })
    })

    describe("lifecycle", () => {
        describe("updated", () => {
            it("should redraw VueMasonry", (done) => {
                let target = mount(AuthorBar, {propsData: {contentId: 1}, store})
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
