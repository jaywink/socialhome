import {mount} from "avoriaz"

import Vue from "vue"
import VueMasonryPlugin from "vue-masonry"

import {getStore} from "streams/app/tests/fixtures/store.fixtures"
import RepliesContainer from "streams/app/components/RepliesContainer.vue"


Vue.use(VueMasonryPlugin)

describe("RepliesContainer", () => {
    let store

    beforeEach(() => {
        store = getStore()
    })

    describe("computer", () => {
        it("isUserAuthenticated", () => {
            let target = mount(RepliesContainer, {propsData: {contentId: store.state.contentIds[0]}, store})
            target.instance().isUserAuthenticated.should.be.true
        })
    })

    describe("methods", () => {

    })

    describe("mountedmo", () => {

    })
})
