import {mount} from "avoriaz"

import Vue from "vue"
import BootstrapVue from "bootstrap-vue"

import StreamElement from "streams/app/components/StreamElement.vue"
import {newStreamStore} from "streams/app/stores/streamStore"
import applicationStore from "streams/app/stores/applicationStore"


Vue.use(BootstrapVue)

describe("StreamElement", () => {
    beforeEach(() => {
        Sinon.restore()
    })

    describe("methods", () => {
        describe("emitLoadMore", () => {
            it("should emit a 'load-more' event if attached content is fifth last", () => {
                let store = newStreamStore({modules: {applicationStore}})
                store.state.streamName = "followed"
                store.state.contentIds = [1, 2, 3, 4, 5]
                store.state.contents = {5: {through: 12}}
                let target = mount(StreamElement, {store, propsData: {contentId: 1}})
                Sinon.spy(target.instance(), "$emit")

                target.instance().emitLoadMore()
                target.instance().$emit.getCall(0).args.should.eql(["load-more"])
            })

            it("should not emit a 'load-more' event if attached content is not fifth last", () => {
                let store = newStreamStore({modules: {applicationStore}})
                store.state.streamName = "followed"
                store.state.contentIds = [1, 2, 3, 4, 5]
                store.state.contents = {5: {through: 12}}
                let target = mount(StreamElement, {store, propsData: {contentId: 12}})
                Sinon.spy(target.instance(), "$emit")

                target.instance().emitLoadMore()
                target.instance().$emit.called.should.be.false
            })
        })
    })
})
