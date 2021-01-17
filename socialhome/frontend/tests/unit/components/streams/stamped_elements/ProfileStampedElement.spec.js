import {mount} from "avoriaz"

import BootstrapVue from "bootstrap-vue"
import Vue from "vue"
import Vuex from "vuex"
import ProfileStampedElement from "@/components/streams/stamped_elements/ProfileStampedElement.vue"
import {getContext} from "%fixtures/jsonContext.fixtures"

import {getStore} from "../../../fixtures/store.fixtures"

Vue.use(BootstrapVue)
Vue.use(Vuex)

describe("ProfileStampedElement", () => {
    let store

    beforeEach(() => {
        store = getStore()
        window.context = getContext({currentBrowsingProfileId: 26})
    })

    describe("computed", () => {
        describe("displayName", () => {
            it("should return name if set", () => {
                store.state.application.profile.name = "Karl Marx"
                const target = mount(ProfileStampedElement, {store})

                target.instance().displayName.should.eql("Karl Marx")
            })

            it("should return FID if name is unset", () => {
                store.state.application.profile.name = undefined
                store.state.application.profile.fid = "http://example.com/profile"
                const target = mount(ProfileStampedElement, {store})

                target.instance().displayName.should.eql("http://example.com/profile")
            })
        })

        describe("showProfileButtons", () => {
            it("should be false if user is not authenticated", () => {
                store.state.application.profile.id = 42
                store.state.application.currentBrowsingProfileId = 42
                store.state.application.isUserAuthenticated = false
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileButtons.should.be.false
            })

            it("should be false if user is not visiting own profile", () => {
                store.state.application.profile.id = 42
                store.state.application.currentBrowsingProfileId = 51
                store.state.application.isUserAuthenticated = true
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileButtons.should.be.false
            })

            it("should be true if user is visiting own profile", () => {
                store.state.application.profile.id = 42
                store.state.application.currentBrowsingProfileId = 42
                store.state.application.isUserAuthenticated = true
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileButtons.should.be.true
            })
        })

        describe("showProfileReactionButtons", () => {
            it("should be false if user is not authenticated", () => {
                store.state.application.profile.id = 42
                store.state.application.currentBrowsingProfileId = 42
                store.state.application.isUserAuthenticated = false
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileReactionButtons.should.be.false
            })

            it("should be true if user is not visiting own profile", () => {
                store.state.application.profile.id = 42
                store.state.application.currentBrowsingProfileId = 51
                store.state.application.isUserAuthenticated = true
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileReactionButtons.should.be.true
            })

            it("should be false if user is visiting own profile", () => {
                store.state.application.profile.id = 42
                store.state.application.currentBrowsingProfileId = 42
                store.state.application.isUserAuthenticated = true
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileReactionButtons.should.be.false
            })
        })
    })
})
