import Axios from "axios"
import Moxios from "moxios"
import Vue from "vue"
import VueMasonryPlugin from "vue-masonry"
import VueSnotify from "vue-snotify"
import BootstrapVue from "bootstrap-vue"
import {mount} from "avoriaz"

import ProfileReactionButtons from "frontend/components/streams/ProfileReactionButtons.vue"
import {getStore} from "frontend/tests/fixtures/store.fixtures"


Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)
Vue.use(VueSnotify)

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
                        uuid: store.content.author.uuid,
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

            it("should show an error to the user if request fails", done => {
                const target = mount(ProfileReactionButtons, {
                    propsData: {
                        profile: store.content.author,
                        userFollowing: false,
                    },
                    store,
                })

                Sinon.spy(target.instance().$snotify, "error")
                target.instance().following.should.be.false
                target.instance().follow()
                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 500}).then(() => {
                        target.instance().$snotify.error.getCall(0).args[0]
                            .should.eq(`An error happened while trying to follow ${store.content.author.name}`)
                        done()
                    })
                })
            })

            it("should show an error to the user if not logged in", () => {
                const target = mount(ProfileReactionButtons, {
                    propsData: {
                        profile: store.content.author,
                        userFollowing: false,
                    },
                    store,
                })

                target.instance().$store.state.applicationStore.isUserAuthenticated = false

                Sinon.spy(target.instance().$snotify, "error")
                target.instance().following.should.be.false
                target.instance().follow()

                target.instance().$snotify.error.getCall(0).args[0].should.eq("You must be logged in to follow someone")
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
                        uuid: store.content.author.uuid,
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

            it("should show an error to the user if request fails", done => {
                const target = mount(ProfileReactionButtons, {
                    propsData: {
                        profile: store.content.author,
                        userFollowing: true,
                    },
                    store,
                })

                Sinon.spy(target.instance().$snotify, "error")
                target.instance().following.should.be.true
                target.instance().unfollow()
                Moxios.wait(() => {
                    Moxios.requests.mostRecent().respondWith({status: 500}).then(() => {
                        target.instance().$snotify.error.getCall(0).args[0]
                            .should.eq(`An error happened while trying to unfollow ${store.content.author.name}`)
                        done()
                    })
                })
            })

            it("should show an error to the user if not logged in", () => {
                const target = mount(ProfileReactionButtons, {
                    propsData: {
                        profile: store.content.author,
                        userFollowing: true,
                    },
                    store,
                })

                target.instance().$store.state.applicationStore.isUserAuthenticated = false

                Sinon.spy(target.instance().$snotify, "error")
                target.instance().following.should.be.true
                target.instance().unfollow()

                target.instance().$snotify.error.getCall(0).args[0]
                    .should.eq("You must be logged in to unfollow someone")
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
