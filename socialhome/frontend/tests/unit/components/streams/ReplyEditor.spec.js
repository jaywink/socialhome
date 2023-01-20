import {mount} from "avoriaz"
import Vue from "vue"
import Vuex from "vuex"
import BootstrapVue from "bootstrap-vue"
import {VueMasonryPlugin} from "vue-masonry"

import ReplyEditor from "@/components/streams/ReplyEditor.vue"
import {getStore} from "%fixtures/store.fixtures"

Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)
Vue.use(Vuex)

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
            const target = mount(ReplyEditor, {
                propsData: {
                    contentId: store.content.id,
                    contentVisibility: store.content.visibility,
                },
                store,
            })
            target.instance().fullEditorUrl.should.eql(`/content/${store.content.id}/~reply/`)
        })
    })

    describe("methods", () => {
        context("saveReply", () => {
            it("dispatches saveReply", () => {
                const target = mount(ReplyEditor, {
                    propsData: {contentId: store.content.id}, store,
                })
                target.setData({replyText: "\"Code without tests doesn't exist\" -Albert Einstein"})
                target.instance().saveReply()
                store.dispatch.callCount.should.eql(1)
                store.dispatch.args[0].should.eql([
                    "stream/saveReply",
                    {
                        data: {
                            parent: store.content.id,
                            text: "\"Code without tests doesn't exist\" -Albert Einstein",
                            recipients: [],
                        },
                    },
                ])
                target.data().replyText.should.eql("")
            })

            it("does not dispatch saveReply if replyText is empty ", () => {
                const target = mount(ReplyEditor, {
                    propsData: {contentId: store.content.id}, store,
                })
                target.setData({replyText: ""})
                target.instance().saveReply()
                store.dispatch.callCount.should.eql(0)
            })
        })
    })

    describe("template", () => {
        it("has a save button", () => {
            const target = mount(ReplyEditor, {
                propsData: {
                    contentId: store.content.id,
                    contentVisibility: store.content.visibility,
                },
                store,
            })
            target.find("button").length.should.eql(1)
        })

        it("has a text area", () => {
            const target = mount(ReplyEditor, {
                propsData: {
                    contentId: store.content.id,
                    contentVisibility: store.content.visibility,
                },
                store,
            })
            target.find("textarea").length.should.eql(1)
        })
    })
})
