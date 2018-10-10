import {shallow, mount} from "avoriaz"

import Vue from "vue"
import BootstrapVue from "bootstrap-vue"
import VueMasonryPlugin from "vue-masonry"
import uuid from "uuid"

import Stream from "frontend/components/streams/Stream.vue"
import StreamElement from "frontend/components/streams/StreamElement.vue"
import "frontend/components/streams/stamped_elements/PublicStampedElement.vue"
import "frontend/components/streams/stamped_elements/FollowedStampedElement.vue"
import {streamStoreOperations, newStreamStore} from "frontend/stores/streamStore"
import {getStore} from "frontend/tests/fixtures/store.fixtures"
import {getFakeContent} from "frontend/tests/fixtures/jsonContext.fixtures"
import applicationStore from "frontend/stores/applicationStore"


Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)


const UUID = uuid()

describe("Stream", () => {
    let store

    beforeEach(() => {
        Sinon.restore()
        store = getStore()
    })

    describe("methods", () => {
        describe("onNewContentClick", () => {
            it("should show the new content button when the user receives new content", done => {
                store.state.stream.name = "" // Deactivate posts fetching
                const target = mount(Stream, {store})
                target.find(".new-content-container")[0].hasStyle("display", "none").should.be.true
                target.instance().$store.commit(streamStoreOperations.receivedNewContent, 1)
                target.instance().$nextTick(() => {
                    target.find(".new-content-container")[0].hasStyle("display", "none").should.be.false
                    target.find(".new-content-container .badge")[0].text().should.match(/1 new post available/)
                    done()
                })
            })

            it("should acknowledge new content when the user clicks the button", () => {
                const target = mount(Stream, {store})
                target.instance().$store.commit(streamStoreOperations.receivedNewContent, 1)
                Sinon.spy(target.instance().$store, "dispatch")
                target.find(".new-content-load-link")[0].trigger("click")
                target.instance().$store.dispatch.getCall(0).args[0].should.eql(streamStoreOperations.newContentAck)
            })
        })

        describe("loadStream", () => {
            beforeEach(() => {
                store = getStore()
                Sinon.spy(store, "dispatch")
            })

            context("store.dispatch without contents", () => {
                beforeEach(() => {
                    store.state.contentIds = []
                    store.state.applicationStore = {profile: {uuid: UUID}}
                })

                it("followed stream with no contents", () => {
                    store.state.stream = {name: "followed"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql([streamStoreOperations.getFollowedStream, {params: {}, data: {}}])
                })

                it("public stream with no contents", () => {
                    store.state.stream = {name: "public"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql([streamStoreOperations.getPublicStream, {params: {}, data: {}}])
                })

                it("tag stream with no contents", () => {
                    store.state.stream = {name: "tag"}
                    mount(Stream, {store, propsData: {tag: "eggs"}})
                    store.dispatch.getCall(0).args.should
                        .eql([streamStoreOperations.getTagStream, {params: {name: "eggs"}, data: {}}])
                })

                it("profile all stream with no contents", () => {
                    store.state.stream = {name: "profile_all"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql([streamStoreOperations.getProfileAll, {params: {uuid: UUID}, data: {}}])
                })

                it("profile pinned stream with no contents", () => {
                    store.state.stream = {name: "profile_pinned"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql([streamStoreOperations.getProfilePinned, {params: {uuid: UUID}, data: {}}])
                })

            })

            context("store.dispatch with contents", () => {
                beforeEach(() => {
                    store.state.contentIds = ["1", "2"]
                    store.state.contents = {"1": {through: "3"}, "2": {through: "4"}}
                    store.state.applicationStore = {profile: {uuid: UUID}}
                })

                it("followed stream with contents", () => {
                    store.state.stream = {name: "followed"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql([streamStoreOperations.getFollowedStream, {params: {lastId: "4"}, data: {}}])
                })

                it("public stream with contents", () => {
                    store.state.stream = {name: "public"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should
                        .eql([streamStoreOperations.getPublicStream, {params: {lastId: "4"}, data: {}}])
                })

                it("tag stream with contents", () => {
                    store.state.stream = {name: "tag"}
                    mount(Stream, {store, propsData: {tag: "eggs"}})
                    store.dispatch.getCall(0).args.should.eql(
                        [streamStoreOperations.getTagStream, {params: {name: "eggs", lastId: "4"}, data: {}}],
                    )
                })

                it("profile all stream with contents", () => {
                    store.state.stream = {name: "profile_all"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should.eql(
                        [streamStoreOperations.getProfileAll, {params: {uuid: UUID, lastId: "4"}, data: {}}],
                    )
                })

                it("profile pinned stream with contents", () => {
                    store.state.stream = {name: "profile_pinned"}
                    mount(Stream, {store})
                    store.dispatch.getCall(0).args.should.eql(
                        [streamStoreOperations.getProfilePinned, {params: {uuid: UUID, lastId: "4"}, data: {}}],
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
                store.state.stream.single = true
                const spy = Sinon.spy(Stream.options.methods, "loadStream")
                mount(Stream, {store})
                spy.called.should.be.false
            })
        })

        describe("render", () => {
            it("should not render unfetched content", () => {
                store = newStreamStore({modules: {applicationStore}})
                store.state.stream.name = ""
                const target = mount(Stream, {store})
                target.find(".grid-item").length.should.eq(0)
                target.instance().$store.commit(streamStoreOperations.receivedNewContent, 1)
                target.find(".grid-item").length.should.eq(0)
            })
        })
    })

    describe("template", () => {
        it("renders single content if single stream", () => {
            // Shallow mount fails with
            // TypeError: key.charAt is not a function
            // Meh :(
            const secondContent = getFakeContent()
            store.state.contents[secondContent.id] = secondContent
            store.state.contentIds.push(secondContent.id)
            let target = mount(Stream, {store})
            target.find(".container").length.should.eql(0)
            target.find(".grid-item-full").length.should.eql(0)
            target.find(".grid-item").length.should.eql(2)

            // Single content stream
            store.state.stream.single = true
            const content = getFakeContent()
            store.state.singleContentId = content.id
            store.state.contents[content.id] = content
            target = mount(Stream, {store})
            target.find(".container").length.should.eql(1)
            target.find(".grid-item-full").length.should.eql(1)
            target.find(".grid-item").length.should.eql(1)
        })
    })
})
