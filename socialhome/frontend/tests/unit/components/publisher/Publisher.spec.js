import BootstrapVue from "bootstrap-vue"

import {createLocalVue, shallowMount} from "@vue/test-utils"
import Publisher from "@/components/publisher/Publisher"
import {getStore} from "%fixtures/store.fixtures"

const localVue = createLocalVue()
localVue.use(BootstrapVue)

describe("Publisher", () => {
    let store

    beforeEach(() => {
        Sinon.restore()
        store = getStore()
    })

    describe("computed", () => {
        it("should display the correct title", () => {
            shallowMount(Publisher, {localVue}).vm.titleText.should.eq("Create")
        })
    })

    describe("onPostForm", () => {
        it("should publish post", () => {
            store.dispatch = Sinon.stub()
            store.dispatch.returns(Promise.resolve())
            const target = shallowMount(Publisher, {
                store,
                localVue,
            })
            target.vm.onPostForm()
            store.dispatch.getCall(0).args.should.eql([
                "publisher/publishPost", {
                    federate: true,
                    includeFollowing: false,
                    pinned: false,
                    recipients: [],
                    showPreview: true,
                    text: "",
                    visibility: 0,
                },
            ])
        })
    })
})
