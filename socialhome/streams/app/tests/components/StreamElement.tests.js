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
                let target = mount(StreamElement, {store, propsData: {contentId: 1}})
                Sinon.spy(target.instance(), "$emit")

                target.instance().emitLoadMore()
                target.instance().$emit.getCall(0).args.should.eql(["load-more"])
            })
        })
    })
})
