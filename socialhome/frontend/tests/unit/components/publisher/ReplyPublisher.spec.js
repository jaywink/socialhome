import BootstrapVue from "bootstrap-vue"
import {shallowMount, createLocalVue} from "@vue/test-utils"
import ReplyPublisher from "@/components/publisher/ReplyPublisher"
import {getStore} from "%fixtures/store.fixtures"

const localVue = createLocalVue()
localVue.use(BootstrapVue)

describe("ReplyPublisher", () => {
    let store

    beforeEach(() => {
        Sinon.restore()
        store = getStore()
    })

    describe("computed", () => {
        it("should display the correct title", () => {
            shallowMount(ReplyPublisher, {localVue}).vm.titleText.should.eq("Reply")
        })
    })

    describe("onPostForm", () => {
        it("should publish post", () => {
            store.dispatch = Sinon.stub()
            store.dispatch.returns(Promise.resolve())
            const target = shallowMount(ReplyPublisher, {
                propsData: {parentId: 12},
                store,
                localVue,
            })
            target.vm.onPostForm()
            store.dispatch.getCall(0).args.should.eql([
                "publisher/publishReply", {
                    parent: 12,
                    recipients: [],
                    showPreview: true,
                    text: "",
                },
            ])
        })
    })
})
