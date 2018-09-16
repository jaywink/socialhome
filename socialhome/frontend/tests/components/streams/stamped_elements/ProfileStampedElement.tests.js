import {mount} from "avoriaz"
import {getContext} from "frontend/tests/fixtures/jsonContext.fixtures"

import BootstrapVue from "bootstrap-vue"
import Vue from "vue"
import Vuex from "vuex"

import ProfileStampedElement from "frontend/components/streams/stamped_elements/ProfileStampedElement.vue"
import {newApplicationStore} from "frontend/stores/applicationStore"


Vue.use(BootstrapVue)
Vue.use(Vuex)

describe("ProfileStampedElement", () => {
    beforeEach(() => {
        window.context = getContext({currentBrowsingProfileId: 26})
    })

    describe("computed", () => {
        describe("displayName", () => {
            it("should return name if set", () => {
                window.context.profile.name = "Karl Marx"
                const store = new Vuex.Store({
                    state: {},
                    modules: {applicationStore: newApplicationStore()}
                })
                const target = mount(ProfileStampedElement, {store})

                target.instance().displayName.should.eql("Karl Marx")
            })

            it("should return FID if name is unset", () => {
                window.context.profile.name = undefined
                window.context.profile.fid = "http://example.com/profile"
                const store = new Vuex.Store({
                    state: {},
                    modules: {applicationStore: newApplicationStore()}
                })
                const target = mount(ProfileStampedElement, {store})

                target.instance().displayName.should.eql("http://example.com/profile")
            })
        })

        describe("showProfileButtons", () => {
            it("should be false if user is not authenticated", () => {
                window.context.profile.id = 42
                window.context.currentBrowsingProfileId = 42
                window.context.isUserAuthenticated = false
                const store = new Vuex.Store({
                    state: {},
                    modules: {applicationStore: newApplicationStore()}
                })
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileButtons.should.be.false
            })

            it("should be false if user is not visiting own profile", () => {
                window.context.profile.id = 42
                window.context.currentBrowsingProfileId = 51
                window.context.isUserAuthenticated = true
                const store = new Vuex.Store({
                    state: {},
                    modules: {applicationStore: newApplicationStore()}
                })
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileButtons.should.be.false
            })

            it("should be true if user is visiting own profile", () => {
                window.context.profile.id = 42
                window.context.currentBrowsingProfileId = 42
                window.context.isUserAuthenticated = true
                const store = new Vuex.Store({
                    state: {},
                    modules: {applicationStore: newApplicationStore()}
                })
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileButtons.should.be.true
            })
        })

        describe("showProfileReactionButtons", () => {
            it("should be false if user is not authenticated", () => {
                window.context.profile.id = 42
                window.context.currentBrowsingProfileId = 42
                window.context.isUserAuthenticated = false
                const store = new Vuex.Store({
                    state: {},
                    modules: {applicationStore: newApplicationStore()}
                })
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileReactionButtons.should.be.false
            })

            it("should be true if user is not visiting own profile", () => {
                window.context.profile.id = 42
                window.context.currentBrowsingProfileId = 51
                window.context.isUserAuthenticated = true
                const store = new Vuex.Store({
                    state: {},
                    modules: {applicationStore: newApplicationStore()}
                })
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileReactionButtons.should.be.true
            })

            it("should be false if user is visiting own profile", () => {
                window.context.profile.id = 42
                window.context.currentBrowsingProfileId = 42
                window.context.isUserAuthenticated = true
                const store = new Vuex.Store({
                    state: {},
                    modules: {applicationStore: newApplicationStore()}
                })
                const target = mount(ProfileStampedElement, {store})

                target.instance().showProfileReactionButtons.should.be.false
            })
        })
    })
})
