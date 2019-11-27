import BootstrapVue from "bootstrap-vue"
import {shallowMount, createLocalVue} from "@vue/test-utils"

import Publisher from "@/components/publisher/Publisher"
import store from "@/store"


const localVue = createLocalVue()
localVue.use(BootstrapVue)

describe("Publisher", () => {
    beforeEach(() => {
        Sinon.restore()
    })

    describe("computed", () => {
        it("should display the correct title", () => {
            shallowMount(Publisher, {localVue}).instance().titleText.should.eq("Reply")
        })
    })

    describe("onPostForm", () => {
        it("should publish post", () => {
            const target = shallowMount(Publisher, {store, localVue})
            Sinon.spy(target.instance().$store, "dispatch")
            target.instance().onPostForm()
            target.instance().$store.dispatch.getCall(0).args.should.eql([
                "publisher/publishPost", {
                    federate: true,
                    includeFollowing: false,
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
