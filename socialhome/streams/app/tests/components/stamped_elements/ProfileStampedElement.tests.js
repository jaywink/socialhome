import {mount} from "avoriaz"
import {getContext} from "streams/app/tests/fixtures/jsonContext.fixtures"

import BootstrapVue from "bootstrap-vue"
import Vue from "vue"
import Vuex from "vuex"

import ProfileStampedElement from "streams/app/components/stamped_elements/ProfileStampedElement.vue"
import {newApplicationStore} from "streams/app/stores/applicationStore"


Vue.use(BootstrapVue)
Vue.use(Vuex)

describe("ProfileStampedElement", () => {
    beforeEach(() => {
        window.context = getContext({currentBrowsingProfileId: 26})
    })

    describe("computed", () => {
        describe("nameOrGuid", () => {
            it("should return name if set", () => {
                window.context.profile.name = "Karl Marx"
                const store = new Vuex.Store({
                    state: {},
                    modules: {applicationStore: newApplicationStore()}
                })
                const target = mount(ProfileStampedElement, {store})

                target.instance().nameOrGuid.should.eql("Karl Marx")
            })

            it("should return GUID if name is unset", () => {
                window.context.profile.name = undefined
                window.context.profile.guid = "123456789"
                const store = new Vuex.Store({
                    state: {},
                    modules: {applicationStore: newApplicationStore()}
                })
                const target = mount(ProfileStampedElement, {store})

                target.instance().nameOrGuid.should.eql("123456789")
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
