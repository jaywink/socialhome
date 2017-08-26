import {mount} from "avoriaz"
import moxios from "moxios"

import Axios from "axios"
import BootstrapVue from "bootstrap-vue"
import Vue from "vue"
import VueMasonryPlugin from "vue-masonry"

import AuthorBar from "streams/app/components/AuthorBar.vue"
import {getAuthorBarPropsData} from "streams/app/tests/fixtures/AuthorBar.fixtures"


Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)

describe("AuthorBar", () => {
    beforeEach(() => {
        Sinon.restore()
    })

    describe("computed", () => {
        describe("isUserRemote", () => {
            it("should be the opposite of property isUserLocal", () => {
                let propsData = getAuthorBarPropsData({isUserLocal: true})
                let target = new AuthorBar({propsData})
                target.isUserRemote.should.be.false

                propsData = getAuthorBarPropsData({isUserLocal: false})
                target = new AuthorBar({propsData})
                target.isUserRemote.should.be.true
            })
        })

        describe("canFollow", () => {
            it("should be true if user is authenticated and not the author", () => {

                let propsData = getAuthorBarPropsData({isUserAuthor: true})
                let target = mount(AuthorBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = false
                target.instance().canFollow.should.be.false

                propsData = getAuthorBarPropsData({isUserAuthor: true})
                target = mount(AuthorBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = true
                target.instance().canFollow.should.be.false

                propsData = getAuthorBarPropsData({isUserAuthor: false})
                target = mount(AuthorBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = true
                target.instance().canFollow.should.be.true
            })
        })

        describe("showFollowBtn and showUnfollowBtn", () => {
            it("should show the follow button when the user can and is not following the author", () => {
                let propsData = getAuthorBarPropsData({isUserAuthor: false, isUserFollowingAuthor: false})
                let target = mount(AuthorBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = true
                target.instance().showFollowBtn.should.be.true
                target.instance().showUnfollowBtn.should.not.be.true
                target.find(".follow-btn").length.should.equal(1)
            })

            it("should show the unfollow button when the user can and is not following the author", () => {
                let propsData = getAuthorBarPropsData({isUserAuthor: false, isUserFollowingAuthor: true})
                let target = mount(AuthorBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = true
                target.instance().showFollowBtn.should.not.be.true
                target.instance().showUnfollowBtn.should.be.true
                target.find(".unfollow-btn").length.should.equal(1)
            })
        })
    })

    describe("methods", () => {
        beforeEach(() => {
            Vue.prototype.$http = Axios.create({
                xsrfCookieName: "csrftoken",
                xsrfHeaderName: "X-CSRFToken",
            })
            moxios.install(Vue.prototype.$http)
        })

        afterEach(() => {
            moxios.uninstall()
        })

        describe("profileBoxTrigger", () => {
            it("should hide profilebox by default", () => {
                let propsData = getAuthorBarPropsData()
                let target = mount(AuthorBar, {propsData})
                target.instance().showProfileBox.should.be.false
                target.find(".profile-box")[0].hasStyle("display", "none").should.be.true
            })

            it("should show profilebox when the author's name is clicked", () => {
                let propsData = getAuthorBarPropsData()
                let target = mount(AuthorBar, {propsData})
                Sinon.spy(target.instance(), "profileBoxTrigger")
                target.find(".profilebox-trigger")[0].trigger("click")
                target.instance().profileBoxTrigger.calledOnce.should.be.true
                target.instance().showProfileBox.should.be.true
                target.find(".profile-box")[0].hasAttribute("display", "none").should.be.false
            })
        })

        describe("unfollow", () => {
            it("should display an error message if the user is not logged in", () => {
                let propsData = getAuthorBarPropsData()
                let target = mount(AuthorBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = false
                Sinon.spy(console, "error")
                target.instance().unfollow()
                console.error.calledWith("Not logged in").should.be.true
            })

            it("should not send an HTTP request if the user is not logged in", () => {
                let propsData = getAuthorBarPropsData()
                let target = mount(AuthorBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = false
                Sinon.spy(target.instance().$http, "post")
                target.instance().unfollow()
                target.instance().$http.post.called.should.be.false
            })

            it("should send an HTTP request with the right parameters when user is logged in", () => {
                let propsData = getAuthorBarPropsData({guid: "42"})
                let target = mount(AuthorBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = true
                target.instance().$store.state.currentBrowsingProfileId = 26

                Sinon.spy(target.instance().$http, "post")
                target.instance().unfollow()
                target.instance().$http.post.getCall(0).args
                    .should.eql(["/api/profiles/26/remove_follower/", {guid: "42"}])
            })

            it("should show that user is following author when the HTTP request succeeds", () => {
                let propsData = getAuthorBarPropsData({
                    currentBrowsingProfileId: "26",
                    guid: "42",
                    isUserAuthor: false,
                    isUserFollowingAuthor: true,
                })

                let target = mount(AuthorBar, {propsData})
                target.instance().unfollow()

                moxios.wait(() => {
                    moxios.requests.mostRecent().respondWith({statusCode: 200}).then(() => {
                        target.instance().$data._isUserFollowingAuthor.should.be.false
                        target.instance().$nextTick(() => {
                            target.find(".follow-btn").length.should.equal(1)
                        })
                    })
                })
            })

            it("should show an error message when the HTTP request fails", () => {
                let propsData = getAuthorBarPropsData({
                    currentBrowsingProfileId: "26",
                    guid: "42",
                    isUserAuthor: false,
                    isUserFollowingAuthor: true,
                })
                let target = mount(AuthorBar, {propsData})
                Sinon.spy(console, "error")

                target.instance().unfollow()

                moxios.wait(() => {
                    moxios.requests.mostRecent().respondWith({statusCode: 500}).then(() => {
                        console.error.getCall(0).args[0].should.equal("Error")
                    })
                })
            })
        })

        describe("follow", () => {
            it("should display an error message if the user is not logged in", () => {
                let propsData = getAuthorBarPropsData()
                let target = mount(AuthorBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = false
                Sinon.spy(console, "error")
                target.instance().follow()
                console.error.getCall(0).args[0].should.equal("Not logged in")
            })

            it("should not send an HTTP request if the user is not logged in", () => {
                let propsData = getAuthorBarPropsData()
                let target = mount(AuthorBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = false
                Sinon.spy(target.instance().$http, "post")
                target.instance().follow()
                target.instance().$http.post.called.should.be.false
            })

            it("should send an HTTP request with the right parameters when user is logged in", () => {
                let propsData = getAuthorBarPropsData({guid: "42"})
                let target = mount(AuthorBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = true
                target.instance().$store.state.currentBrowsingProfileId = "26"
                Sinon.spy(target.instance().$http, "post")
                target.instance().follow()
                target.instance().$http.post
                    .calledWith("/api/profiles/26/add_follower/", {guid: "42"}).should.be.true
            })

            it("should show that user is following author when the HTTP request succeeds", () => {
                let propsData = getAuthorBarPropsData({
                    currentBrowsingProfileId: "26",
                    guid: "42",
                    isUserAuthor: false,
                    isUserFollowingAuthor: false,
                })
                let target = mount(AuthorBar, {propsData})
                target.instance().follow()

                moxios.wait(() => {
                    moxios.requests.mostRecent().respondWith({statusCode: 200}).then(() => {
                        target.instance().$data._isUserFollowingAuthor.should.be.false
                        target.instance().$nextTick(() => {
                            target.find(".unfollow-btn").length.should.equal(1)
                        })
                    })
                })
            })

            it("should show an error message when the HTTP request fails", () => {
                let propsData = getAuthorBarPropsData({
                    currentBrowsingProfileId: "26",
                    guid: "42",
                    isUserAuthor: false,
                    isUserFollowingAuthor: true,
                })
                let target = mount(AuthorBar, {propsData})

                Sinon.spy(console, "error")
                target.instance().follow()

                moxios.wait(() => {
                    moxios.requests.mostRecent().respondWith({statusCode: 500}).then(() => {
                        console.error.getCall(0).args[0].should.equal("Error")
                    })
                })
            })
        })
    })

    describe("lifecycle", () => {
        describe("updated", () => {
            it("should redraw VueMasonry", (done) => {
                let propsData = getAuthorBarPropsData()
                let target = mount(AuthorBar, {propsData})
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
