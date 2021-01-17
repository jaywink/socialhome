import Vue from "vue"
import Vuex from "vuex"
import {VueMasonryPlugin} from "vue-masonry"
import VueSnotify from "vue-snotify"
import BootstrapVue from "bootstrap-vue"
import {mount} from "avoriaz"

import ProfileReactionButtons from "@/components/common/ProfileReactionButtons.vue"
import {getStore} from "%fixtures/store.fixtures"

Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)
Vue.use(VueSnotify)
Vue.use(Vuex)

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
                store.content.author.user_following = false
                store.state.application.isUserAuthenticated = true
                const target = mount(ProfileReactionButtons, {
                    propsData: {profileUuid: store.content.author.uuid},
                    store,
                })
                target.instance().showFollowBtn.should.be.true
                target.instance().showUnfollowBtn.should.be.false
                target.find(".follow-btn").length.should.equal(1)
            })

            it("should show the unfollow button when the user can and is not following the author", () => {
                store.content.user_is_author = false
                store.content.author.user_following = true
                store.state.application.isUserAuthenticated = true
                const target = mount(ProfileReactionButtons, {
                    propsData: {profileUuid: store.content.author.uuid},
                    store,
                })
                target.instance().showFollowBtn.should.be.false
                target.instance().showUnfollowBtn.should.be.true
                target.find(".unfollow-btn").length.should.equal(1)
            })
        })
    })

    describe("methods", () => {
        describe("follow", () => {
            it("should dispatch a follow action", () => {
                const target = mount(ProfileReactionButtons, {
                    propsData: {profileUuid: store.content.author.uuid},
                    store,
                })

                Sinon.spy(target.instance().$store, "dispatch")
                target.instance().follow()
                target.instance().$store.dispatch.getCall(0).args.should.eql([
                    "profiles/follow", {uuid: store.content.author.uuid},
                ])
            })
        })

        describe("unfollow", () => {
            it("should dispatch an unfollow action", () => {
                const target = mount(ProfileReactionButtons, {
                    propsData: {profileUuid: store.content.author.uuid},
                    store,
                })

                Sinon.spy(target.instance().$store, "dispatch")
                target.instance().unfollow()
                target.instance().$store.dispatch.getCall(0).args.should.eql([
                    "profiles/unFollow", {uuid: store.content.author.uuid},
                ])
            })
        })
    })
})
