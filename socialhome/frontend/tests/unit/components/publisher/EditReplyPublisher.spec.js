import BootstrapVue from "bootstrap-vue"
import faker from "faker"

import {createLocalVue, shallowMount} from "@vue/test-utils"
import EditReplyPublisher from "@/components/publisher/EditReplyPublisher"
import {getStore} from "%fixtures/store.fixtures"

const localVue = createLocalVue()
localVue.use(BootstrapVue)

describe("EditReplyPublisher", () => {
    let store
    let propsData

    beforeEach(() => {
        Sinon.restore()
        store = getStore()
        propsData = {
            contentId: "12",
            parentId: `${faker.random.number()}`,
            showPreview: faker.random.boolean(),
            text: faker.lorem.paragraphs(4),
        }
    })

    describe("computed", () => {
        it("should display the correct title", () => {
            shallowMount(EditReplyPublisher, {
                localVue,
                propsData,
            }).vm.titleText.should.eq("Update reply")
        })
    })

    describe("onPostForm", () => {
        it("should publish post", () => {
            store.dispatch = Sinon.stub()
            store.dispatch.returns(Promise.resolve())
            const target = shallowMount(EditReplyPublisher, {
                propsData,
                store,
                localVue,
            })
            target.vm.onPostForm()
            store.dispatch.getCall(0).args.should.eql([
                "publisher/editReply", {
                    contentId: "12",
                    parent: propsData.parentId,
                    recipients: [],
                    showPreview: propsData.showPreview,
                    text: propsData.text,
                },
            ])
        })
    })
})
