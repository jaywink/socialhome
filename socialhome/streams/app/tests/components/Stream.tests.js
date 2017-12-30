import {mount} from "avoriaz"

import Vue from "vue"
import BootstrapVue from "bootstrap-vue"
import VueMasonryPlugin from "vue-masonry"

import Stream from "streams/app/components/Stream.vue"
import PublicStampedElement from "streams/app/components/stamped_elements/PublicStampedElement.vue"
import FollowedStampedElement from "streams/app/components/stamped_elements/FollowedStampedElement.vue"
import {streamStoreOperations} from "streams/app/stores/streamStore"
import {getStore} from "streams/app/tests/fixtures/store.fixtures"
import {getFakeContent} from "streams/app/tests/fixtures/jsonContext.fixtures"
import applicationStore from "../../stores/applicationStore"
import {newStreamStore} from "../../stores/streamStore"


Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)

describe("Stream", () => {
    let store

    beforeEach(() => {
        Sinon.restore()
        store = getStore()
    })

    describe("computed", () => {
        describe("stampedElement", () => {
            it("should render the FollowedStampedElement when stream name is 'followed'", () => {
                store.state.stream.name = "followed"
                let target = mount(Stream, {store})
                target.instance().stampedElement.should.eq("FollowedStampedElement")
            })

            it("should render the PublicStampedElement when stream name is 'public'", () => {
                store.state.stream.name = "public"
                let target = mount(Stream, {store})
                target.instance().stampedElement.should.eq("PublicStampedElement")
            })

            it("should render the TagStampedElement when stream name is 'tag'", () => {
                store.state.stream.name = "tag"
                let target = mount(Stream, {store})
                target.instance().stampedElement.should.eq("TagStampedElement")
            })

            it("should render the ProfileStampedElement when stream name is 'profile'", () => {
                store.state.stream.name = "profile_all"
                let target = mount(Stream, {store})
                target.instance().stampedElement.should.eq("ProfileStampedElement")
                store.state.stream.name = "profile_pinned"
                target = mount(Stream, {store})
                target.instance().stampedElement.should.eq("ProfileStampedElement")
            })

            it("should display an error when stream name is unknown", () => {
                store.state.stream.name = "Yolo stream"
                Sinon.spy(console, "error")
                let target = mount(Stream, {store})
                target.instance().stampedElement
                console.error.getCall(0).args[0].should.eq("Unsupported stream name Yolo stream")
            })
        })
    })

    describe("methods", () => {
        describe("onNewContentClick", () => {
            it("should show the new content button when the user receives new content", (done) => {
                store.state.stream.name = "" // Deactivate posts fetching
                let target = mount(Stream, {store})
                target.find(".new-content-container")[0].hasStyle("display", "none").should.be.true
                target.instance().$store.commit(streamStoreOperations.receivedNewContent, 1)
                target.instance().$nextTick(() => {
                    target.find(".new-content-container")[0].hasStyle("display", "none").should.be.false
                    target.find(".new-content-container .badge")[0].text().should.match(/1 new post available/)
                    done()
                })
            })

            it("should acknowledge new content when the user clicks the button", () => {
                let target = mount(Stream, {store})
                target.instance().$store.commit(streamStoreOperations.receivedNewContent, 1)
                Sinon.spy(target.instance().$store, "dispatch")
                target.find(".new-content-load-link")[0].trigger("click")
                target.instance().$store.dispatch.getCall(0).args[0].should.eql(streamStoreOperations.newContentAck)
            })
        })
    })

    describe("Lifecycle", () => {
        describe("beforeCreate", () => {
            it("loads stream if not single stream", () => {
                Sinon.spy(store, "dispatch")
                let target = mount(Stream, {store})
                target.instance().$store.dispatch.getCall(0).args[0].should.eql(streamStoreOperations.loadStream)
            })

            it("does not load stream if single stream", () => {
                // This causes nasty traceback due to repliescontainer trying to fetch replies
                // But shallow mount wont work for some reason with our Stream component
                store.state.stream.single = true
                Sinon.spy(store, "dispatch")
                let target = mount(Stream, {store})
                target.instance().$store.dispatch.called.should.be.false
            })
        })

        describe("render", () => {
            it("should not render unfetched content", () => {
                store = newStreamStore({modules: {applicationStore}})
                store.state.stream.name = ""
                let target = mount(Stream, {store})
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
