import Vue from "vue"
import Vuex from "vuex"
import BootstrapVue from "bootstrap-vue"
import {VueMasonryPlugin} from "vue-masonry"
import uuid from "uuid/v4"
import {mount} from "avoriaz"

import Stream from "@/components/streams/Stream.vue"
import "@/components/streams/stamped_elements/PublicStampedElement.vue"
import "@/components/streams/stamped_elements/FollowedStampedElement.vue"
import {getStore} from "%fixtures/store.fixtures"

Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)
Vue.use(Vuex)

const UUID = uuid()

describe("Stream", () => {
    let store

    beforeEach(() => {
        store = getStore()
        Sinon.spy(store, "dispatch")
    })

    afterEach(() => {
        Sinon.restore()
    })

    describe("methods", () => {
        describe("loadStream", () => {
            context("store.dispatch without contents", () => {
                beforeEach(() => {
                    store.state.stream.contentIds = []
                    store.state.application = {profile: {uuid: UUID}}
                })

                it("followed stream with no contents", () => {
                    store.state.stream.stream = {name: "followed"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql(["stream/getFollowedStream", {params: {}}])
                })

                it("public stream with no contents", () => {
                    store.state.stream.stream = {name: "public"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql(["stream/getPublicStream", {params: {}}])
                })

                it("tag stream with no contents", () => {
                    store.state.stream.stream = {name: "tag"}
                    mount(Stream, {store, propsData: {tag: "eggs"}})
                    store.dispatch.getCall(0).args.should
                        .eql(["stream/getTagStream", {params: {name: "eggs"}}])
                })

                it("profile all stream with no contents", () => {
                    store.state.stream.stream = {name: "profile_all"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql(["stream/getProfileAll", {params: {uuid: UUID}}])
                })

                it("profile pinned stream with no contents", () => {
                    store.state.stream.stream = {name: "profile_pinned"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql(["stream/getProfilePinned", {params: {uuid: UUID}}])
                })
            })

            context("store.dispatch with contents", () => {
                beforeEach(() => {
                    store.state.stream.contentIds = ["1", "2"]
                    store.state.stream.contents = {1: {through: "3"}, 2: {through: "4"}}
                    store.state.application = {profile: {uuid: UUID}}
                })

                it("followed stream with contents", () => {
                    store.state.stream.stream = {name: "followed"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql(["stream/getFollowedStream", {params: {lastId: "4"}}])
                })

                it("public stream with contents", () => {
                    store.state.stream.stream = {name: "public"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql(["stream/getPublicStream", {params: {lastId: "4"}}])
                })

                it("tag stream with contents", () => {
                    store.state.stream.stream = {name: "tag"}
                    mount(Stream, {store, propsData: {tag: "eggs"}})
                    store.dispatch.getCall(0).args.should.eql(
                        ["stream/getTagStream", {params: {name: "eggs", lastId: "4"}}],
                    )
                })

                it("profile all stream with contents", () => {
                    store.state.stream.stream = {name: "profile_all"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should.eql(
                        ["stream/getProfileAll", {params: {uuid: UUID, lastId: "4"}}],
                    )
                })

                it("profile pinned stream with contents", () => {
                    store.state.stream.stream = {name: "profile_pinned"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should.eql(
                        ["stream/getProfilePinned", {params: {uuid: UUID, lastId: "4"}}],
                    )
                })
            })
        })
    })

    describe("Lifecycle", () => {
        describe("beforeMount", () => {
            it("loads stream if not single stream", () => {
                const spy = Sinon.spy(Stream.options.methods, "loadStream")
                mount(Stream, {store})
                spy.calledOnce.should.be.true
            })

            it("does not load stream if single stream", () => {
                // This causes nasty traceback due to repliescontainer trying to fetch replies
                // But shallow mount wont work for some reason with our Stream component
                store.state.stream.stream.single = true
                const spy = Sinon.spy(Stream.options.methods, "loadStream")
                mount(Stream, {store})
                spy.called.should.be.false
            })
        })
    })
})
