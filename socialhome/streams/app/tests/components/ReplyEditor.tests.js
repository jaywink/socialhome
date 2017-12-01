import {mount} from "avoriaz"
import Vue from "vue"
import BootstrapVue from "bootstrap-vue"
import VueMasonryPlugin from "vue-masonry"

import {getStore} from "streams/app/tests/fixtures/store.fixtures"
import {streamStoreOperations} from "streams/app/stores/streamStore.operations"
import ReplyEditor from "streams/app/components/ReplyEditor.vue"

Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)


describe("ReplyEditor", () => {
    let store

    beforeEach(() => {
        store = getStore()
        Sinon.stub(store, "dispatch")
    })

    afterEach(() => {
        Sinon.restore()
    })

    describe("computed", () => {
        it("fullEditorUrl", () => {
            let target = mount(ReplyEditor, {propsData: {contentId: store.content.id}, store})
            target.instance().fullEditorUrl.should.eql(`/content/${store.content.id}/~reply/`)
        })
    })

    describe("methods", () => {
        context("saveReply", () => {
            it("dispatches saveReply", () => {
                let target = mount(ReplyEditor, {propsData: {contentId: store.content.id}, store})
                target.setData({replyText: "\"Code without tests doesn't exist\" -Albert Einstein"})
                target.instance().saveReply()
                store.dispatch.callCount.should.eql(1)
                store.dispatch.args[0].should.eql([
                    streamStoreOperations.saveReply, {
                        data: {parent: store.content.id, text: "\"Code without tests doesn't exist\" -Albert Einstein"}
                    },
                ])
                target.data().replyText.should.eql("")
            })

            it("does not dispatch saveReply if replyText is empty ", () => {
                let target = mount(ReplyEditor, {propsData: {contentId: store.content.id}, store})
                target.setData({replyText: ""})
                target.instance().saveReply()
                store.dispatch.callCount.should.eql(0)
            })
        })
    })

    describe("template", () => {
        it("has a save button", () => {
            let target = mount(ReplyEditor, {propsData: {contentId: store.content.id}, store})
            target.find("button").length.should.eql(1)
        })

        it("has a text area", () => {
            let target = mount(ReplyEditor, {propsData: {contentId: store.content.id}, store})
            target.find("textarea").length.should.eql(1)
        })
    })
})
