import BootstrapVue from "bootstrap-vue"
import {shallowMount, createLocalVue} from "@vue/test-utils"
import EditReplyPublisher from "@/components/publisher/EditReplyPublisher"
import {getStore} from "%fixtures/store.fixtures"


const localVue = createLocalVue()
localVue.use(BootstrapVue)

describe("EditReplyPublisher", () => {
    let store

    beforeEach(() => {
        Sinon.restore()
        store = getStore()
    })

    describe("computed", () => {
        it("should display the correct title", () => {
            shallowMount(EditReplyPublisher, {localVue}).vm.titleText.should.eq("Edit reply")
        })
    })

    describe("onPostForm", () => {
        it("should publish post", () => {
            store.dispatch = Sinon.stub()
            store.dispatch.returns(Promise.resolve())
            const target = shallowMount(EditReplyPublisher, {propsData: {contentId: 12}, store, localVue})
            target.vm.onPostForm()
            store.dispatch.getCall(0).args.should.eql([
                "publisher/publishPost", {
                    federate: true,
                    includeFollowing: false,
                    parent: 12,
                    pinned: false,
                    recipients: "",
                    showPreview: true,
                    text: "",
                    visibility: 0,
                },
            ])
        })
    })
})
