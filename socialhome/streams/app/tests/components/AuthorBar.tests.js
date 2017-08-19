import "chai/register-should"
import {mount} from "avoriaz"
import sinon from "sinon"

import {getPropsData} from "../fixtures/AuthorBar.fixtures"

import Vue from "vue"
import Axios from "axios"
import BootstrapVue from "bootstrap-vue"

import AuthorBar from "streams/app/components/AuthorBar.vue"


Vue.use(BootstrapVue)

describe("AuthorBar", () => {
    describe("computed", () => {
        describe("isUserRemote", () => {
            it("should be the opposite of property isUserLocal", () => {
                let propsData = getPropsData({isUserLocal: true})
                let target = new AuthorBar({propsData})
                target.isUserRemote.should.be.false

                propsData = getPropsData({isUserLocal: false})
                target = new AuthorBar({propsData})
                target.isUserRemote.should.be.true
            })
        })

        describe("canFollow", () => {
            it("sould be true if user is authenticated and not the author", () => {
                let propsData = getPropsData({isUserAuthenticated: false, isUserAuthor: true})
                let target = new AuthorBar({propsData})
                target.canFollow.should.be.false

                propsData = getPropsData({isUserAuthenticated: true, isUserAuthor: true})
                target = new AuthorBar({propsData})
                target.canFollow.should.be.false

                propsData = getPropsData({isUserAuthenticated: true, isUserAuthor: false})
                target = new AuthorBar({propsData})
                target.canFollow.should.be.true
            })
        })

        describe("showFollowBtn and showUnfollowBtn", () => {
            it("should show the follow button when the user can and is not following the author", () => {
                let propsData = getPropsData({isUserAuthor: false, isUserFollowingAuthor: false})
                let target = mount(AuthorBar, {propsData})
                target.instance().showFollowBtn.should.be.true
                target.instance().showUnfollowBtn.should.not.be.true
                target.find(".follow-btn").length.should.equal(1)
            })

            it("should show the unfollow button when the user can and is not following the author", () => {
                let propsData = getPropsData({isUserAuthor: false, isUserFollowingAuthor: true})
                let target = mount(AuthorBar, {propsData})
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
        })

        describe("profileBoxTrigger", () => {
            it("should hide profilebox by default", () => {
                let propsData = getPropsData()
                let target = mount(AuthorBar, {propsData})
                target.instance().showProfileBox.should.be.false
                target.find(".profile-box")[0].hasStyle("display", "none").should.be.true
            })

            it("should show profilebox when the author's name is clicked", () => {
                let propsData = getPropsData()
                let target = mount(AuthorBar, {propsData})
                sinon.spy(target.instance(), "profileBoxTrigger")
                target.find(".profilebox-trigger")[0].trigger("click")
                target.instance().profileBoxTrigger.calledOnce.should.be.true
                target.instance().showProfileBox.should.be.true
                target.find(".profile-box")[0].hasAttribute("display", "none").should.be.false
            })
        })

        describe("unfollow", () => {
            it("should display an error message if the user is not logged in", () => {
                let propsData = getPropsData({currentBrowsingProfileId: void(0)})
                let target = mount(AuthorBar, {propsData})
                sinon.spy(console, "error")
                target.instance().unfollow()
                console.error.calledWith("Not logged in").should.be.true
                console.error.restore()
            })

            it("should not send an HTTP request if the user is not logged in", () => {
                let propsData = getPropsData({currentBrowsingProfileId: void(0)})
                let target = mount(AuthorBar, {propsData})
                sinon.spy(target.instance().$http, "post")
                target.instance().unfollow()
                target.instance().$http.post.called.should.be.false
            })

            it("should send an HTTP request with the right parameters when user is logged in", () => {
                let propsData = getPropsData({currentBrowsingProfileId: "26", guid: "42"})
                let target = mount(AuthorBar, {propsData})
                sinon.spy(target.instance().$http, "post")
                target.instance().unfollow()
                target.instance().$http.post
                    .calledWith("/api/profiles/26/remove_follower/", {guid: "42"}).should.be.true
            })

            it("should show that user is following author when the HTTP request succeeds", () => {
                let propsData = getPropsData({currentBrowsingProfileId: "26", guid: "42", isUserFollowingAuthor: true})
                let target = mount(AuthorBar, {propsData})
                sinon.stub(target.instance().$http, "post").returns(new Promise(resolve => {
                    resolve()
                    target.instance().$data._isUserFollowingAuthor.should.be.false
                    target.find(".follow-btn").length.should.equal(1)
                }))
                target.instance().unfollow()
            })

            it("should show an error message when the HTTP request fails", () => {
                let propsData = getPropsData({currentBrowsingProfileId: "26", guid: "42", isUserFollowingAuthor: true})
                let target = mount(AuthorBar, {propsData})
                sinon.stub(target.instance().$http, "post").returns(new Promise(_, reject => {
                    reject()
                    sinon.spy(console, "error")
                    console.error.calledWith("Not logged in").should.be.true
                    console.error.restore()
                }))
                target.instance().unfollow()
            })
        })

        describe("follow", () => {
            it("should display an error message if the user is not logged in", () => {
                let propsData = getPropsData({currentBrowsingProfileId: null})
                let target = mount(AuthorBar, {propsData})
                sinon.spy(console, "error")
                target.instance().follow()
                console.error.calledWith("Not logged in").should.be.true
                console.error.restore()
            })

            it("should not send an HTTP request if the user is not logged in", () => {
                let propsData = getPropsData({currentBrowsingProfileId: null})
                let target = mount(AuthorBar, {propsData})
                sinon.spy(target.instance().$http, "post")
                target.instance().follow()
                target.instance().$http.post.called.should.be.false
            })

            it("should send an HTTP request with the right parameters when user is logged in", () => {
                let propsData = getPropsData({currentBrowsingProfileId: "26", guid: "42"})
                let target = mount(AuthorBar, {propsData})
                sinon.spy(target.instance().$http, "post")
                target.instance().follow()
                target.instance().$http.post
                    .calledWith("/api/profiles/26/add_follower/", {guid: "42"}).should.be.true
            })

            it("should show that user is following author when the HTTP request succeeds", () => {
                let propsData = getPropsData({currentBrowsingProfileId: "26", guid: "42", isUserFollowingAuthor: false})
                let target = mount(AuthorBar, {propsData})
                sinon.stub(target.instance().$http, "post").returns(new Promise(resolve => {
                    resolve()
                    target.instance().$data._isUserFollowingAuthor.should.be.true
                    target.find(".unfollow-btn").length.should.equal(1)
                }))
                target.instance().follow()
            })

            it("should show an error message when the HTTP request fails", () => {
                let propsData = getPropsData({currentBrowsingProfileId: "26", guid: "42", isUserFollowingAuthor: true})
                let target = mount(AuthorBar, {propsData})
                sinon.stub(target.instance().$http, "post").returns(new Promise(_, reject => {
                    reject()
                    sinon.spy(console, "error")
                    console.error.calledWith("Not logged in").should.be.true
                    console.error.restore()
                }))
                target.instance().follow()
            })
        })
    })

    describe("lifecycle", () => {
        describe("updated", () => {
            it("should redraw VueMasonry", (done) => {
                let propsData = getPropsData()
                let target = mount(AuthorBar, {propsData})
                Vue.redrawVueMasonry = sinon.spy()
                target.update()
                target.vm.$nextTick(() => {
                    Vue.redrawVueMasonry.called.should.be.true
                    done()
                })
            })
        })
    })
})
