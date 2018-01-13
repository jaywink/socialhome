import Axios from "axios"
import BootstrapVue from "bootstrap-vue"
import Moxios from "moxios"
import Vue from "vue"
import VueMasonryPlugin from "vue-masonry"
import {mount} from "avoriaz"

import ProfileReactionButtons from "streams/app/components/ProfileReactionButtons.vue"
import {getStore} from "streams/app/tests/fixtures/store.fixtures"


Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)

describe("ProfileReactionButtons", () => {
    let store

    beforeEach(() => {
        Sinon.restore()
        store = getStore()
    })

    describe("computed", () => {
        describe("showFollowBtn and showUnfollowBtn", () => {
            it("should show the follow button when the user can and is not following the author", () => {
                store.content.user_is_author = false
                store.state.applicationStore.isUserAuthenticated = true
                const target = mount(ProfileReactionButtons, {
                    propsData: {
                        profile: store.content.author,
                        userFollowing: false,
                    },
                    store,
                })
                target.instance().showFollowBtn.should.be.true
                target.instance().showUnfollowBtn.should.be.false
                target.find(".follow-btn").length.should.equal(1)
            })

            it("should show the unfollow button when the user can and is not following the author", () => {
                store.content.user_is_author = false
                store.state.applicationStore.isUserAuthenticated = true
                const target = mount(ProfileReactionButtons, {
                    propsData: {
                        profile: store.content.author,
                        userFollowing: true,
                    },
                    store,
                })
                target.instance().showFollowBtn.should.be.false
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
            Moxios.install(Vue.prototype.$http)
        })

        afterEach(() => {
            Moxios.uninstall()
        })

        describe("follow", () => {
            it("should send an HTTP request with the right parameters", () => {
                const target = mount(ProfileReactionButtons, {
                    propsData: {
                        profile: store.content.author,
                        userFollowing: false,
                    },
                    store,
                })

                Sinon.spy(target.instance().$http, "post")
                target.instance().follow()
                target.instance().$http.post.getCall(0).args
                    .should.eql([`/api/profiles/${store.profile.id}/add_follower/`, {
                        guid: store.content.author.guid,
                    }])
            })

            it("should show that user is following author when the HTTP request succeeds", done => {
                const target = mount(ProfileReactionButtons, {
                    propsData: {
                        profile: store.content.author,
                        userFollowing: false,
                    },
                    store,
                })

                Sinon.spy(target.instance().$http, "post")
                target.instance().following.should.be.false
                target.instance().follow()
                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 200}).then(() => {
                        target.instance().following.should.be.true
                        done()
                    })
                })
            })
        })

        describe("unfollow", () => {
            it("should send an HTTP request with the right parameters", () => {
                const target = mount(ProfileReactionButtons, {
                    propsData: {
                        profile: store.content.author,
                        userFollowing: true,
                    },
                    store,
                })

                Sinon.spy(target.instance().$http, "post")
                target.instance().unfollow()
                target.instance().$http.post.getCall(0).args
                    .should.eql([`/api/profiles/${store.profile.id}/remove_follower/`, {
                        guid: store.content.author.guid,
                    }])
            })

            it("should show that user is not following author when the HTTP request succeeds", done => {
                const target = mount(ProfileReactionButtons, {
                    propsData: {
                        profile: store.content.author,
                        userFollowing: true,
                    },
                    store,
                })

                Sinon.spy(target.instance().$http, "post")
                target.instance().following.should.be.true
                target.instance().unfollow()
                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 200}).then(() => {
                        target.instance().following.should.be.false
                        done()
                    })
                })
            })
        })
    })

    describe("render", () => {
        it("renders with content author object", () => {
            const target = mount(ProfileReactionButtons, {propsData: {profile: store.content.author}, store})
            target.instance().following.should.be.false
        })

        it("renders with profile object", () => {
            const target = mount(ProfileReactionButtons, {propsData: {profile: store.profile}, store})
            target.instance().following.should.be.false
        })
    })
})
