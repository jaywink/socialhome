import BootstrapVue from "bootstrap-vue"
import faker from "faker"

import {createLocalVue, shallowMount} from "@vue/test-utils"
import EditPublisher from "@/components/publisher/EditPublisher"
import {getStore} from "%fixtures/store.fixtures"

const localVue = createLocalVue()
localVue.use(BootstrapVue)

describe("EditPublisher", () => {
    let store
    let propsData

    beforeEach(() => {
        Sinon.restore()
        store = getStore()
        propsData = {
            contentId: 12,
            isReply: faker.random.boolean(),
            federate: faker.random.boolean(),
            includeFollowing: faker.random.boolean(),
            recipients: Array(faker.random.number(5)).map(() => faker.random.email()),
            pinned: faker.random.boolean(),
            showPreview: faker.random.boolean(),
            text: faker.lorem.paragraphs(4),
            visibility: Math.floor((Math.random() * 4)),
        }
    })

    describe("computed", () => {
        it("should display the correct title", () => {
            shallowMount(EditPublisher, {
                localVue,
                propsData,
            }).vm.titleText.should.eq("Edit")
        })
    })

    describe("onPostForm", () => {
        it("should publish post", () => {
            store.dispatch = Sinon.stub()
            store.dispatch.returns(Promise.resolve())
            const target = shallowMount(EditPublisher, {
                propsData,
                store,
                localVue,
            })

            target.vm.onPostForm()
            store.dispatch.getCall(0).args.should.eql([
                "publisher/editPost", {
                    contentId: 12,
                    federate: propsData.federate,
                    includeFollowing: propsData.includeFollowing,
                    pinned: propsData.pinned,
                    recipients: propsData.recipients,
                    showPreview: propsData.showPreview,
                    text: propsData.text,
                    visibility: propsData.visibility,
                },
            ])
        })
    })
})
