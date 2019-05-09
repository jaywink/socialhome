import BootstrapVue from "bootstrap-vue"
import Vue from "vue"
import VueMasonryPlugin from "vue-masonry"
import {mount, shallow} from "avoriaz"

import Publisher from "frontend/components/publisher/Publisher"
import store from "frontend/store"
import Axios from "axios"


Vue.use(BootstrapVue)
Vue.use(VueMasonryPlugin)

describe("Publisher", () => {
    beforeEach(() => {
        Sinon.restore()
        Vue.prototype.$http = Axios.create({
            xsrfCookieName: "csrftoken",
            xsrfHeaderName: "X-CSRFToken",
        })
    })

    describe("computed", () => {
        it("should display the correct title", () => {
            window.context = {isReply: true}
            shallow(Publisher, {propsData: {contentId: "12"}}).instance().titleText.should.eq("Update reply")
            shallow(Publisher).instance().titleText.should.eq("Reply")
            window.context = {isReply: undefined}
            shallow(Publisher, {propsData: {contentId: "12"}}).instance().titleText.should.eq("Reply")
            shallow(Publisher).instance().titleText.should.eq("Create")
        })
    })

    describe("onPostForm", () => {
        it("should publish post", () => {
            const target = mount(Publisher, {propsData: {contentId: "12"}, store})
            Sinon.spy(target.instance().$store, "dispatch")
            target.instance().onPostForm()
            target.instance().$store.dispatch.getCall(0).args.should.eql(["publisher/publishPost", {
                federate: true,
                includeFollowing: false,
                parent: "12",
                pinned: false,
                recipients: "",
                showPreview: true,
                text: "",
                visibility: 0,
            }])
        })
    })
})
