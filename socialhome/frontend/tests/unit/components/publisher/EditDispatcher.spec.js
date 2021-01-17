import BootstrapVue from "bootstrap-vue"
import faker from "faker"

import {createLocalVue, shallowMount} from "@vue/test-utils"
import EditDispatcher from "@/components/publisher/EditDispatcher"

const localVue = createLocalVue()
localVue.use(BootstrapVue)

describe("EditDispatcher", () => {
    let contentId

    beforeEach(() => {
        Sinon.restore()
        contentId = faker.random.word()
        window.context = {
            isReply: faker.random.boolean(),
            federate: faker.random.boolean(),
            includeFollowing: faker.random.boolean(),
            recipients: faker.random.word(),
            parent: faker.random.word(),
            pinned: faker.random.boolean(),
            showPreview: faker.random.boolean(),
            text: faker.lorem.paragraphs(4),
            visibility: Math.floor((Math.random() * 4)),
        }
    })

    describe("computed", () => {
        it("should display the correct component", () => {
            let target
            window.context.isReply = false
            target = shallowMount(EditDispatcher, {
                localVue,
                propsData: {contentId},
            })
            target.vm.component.should.eq("EditPublisher")
            window.context.isReply = true
            target = shallowMount(EditDispatcher, {
                localVue,
                propsData: {contentId},
            })
            target.vm.component.should.eq("EditReplyPublisher")
        })

        it("should display the correctly pass data to the components", () => {
            window.context.isReply = false
            shallowMount(EditDispatcher, {
                localVue,
                propsData: {contentId},
            }).vm.boundValues.should.eql({
                contentId,
                federate: window.context.federate,
                includeFollowing: window.context.includeFollowing,
                pinned: window.context.pinned,
                recipients: window.context.recipients,
                showPreview: window.context.showPreview,
                text: window.context.text,
                visibility: window.context.visibility,
            })
            window.context.isReply = true
            shallowMount(EditDispatcher, {
                localVue,
                propsData: {contentId},
            }).vm.boundValues.should.eql({
                contentId,
                parentId: window.context.parent,
                showPreview: window.context.showPreview,
                text: window.context.text,
            })
        })
    })
})
