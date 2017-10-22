import {mount} from "avoriaz"

import Vue from "vue"
import VueMasonryPlugin from "vue-masonry"

import NsfwShield from "streams/app/components/NsfwShield.vue"


Vue.use(VueMasonryPlugin)

describe("NsfwShield", () => {
    beforeEach(() => {
        Sinon.restore()
    })

    describe("methods", () => {
        describe("toggleNsfwShield", () => {
            it("should toggle `showNsfwContent`", () => {
                let target = mount(NsfwShield, {propsData: {tags: ["nsfw"]}})
                target.instance().showNsfwContent.should.be.false
                target.instance().toggleNsfwShield()
                target.instance().showNsfwContent.should.be.true
                target.instance().toggleNsfwShield()
                target.instance().showNsfwContent.should.be.false
            })

            it("should show and hide content", (done) => {
                let target = mount(NsfwShield, {
                    propsData: {tags: ["nsfw"]},
                    slots: {"default": {template: "<div>This is #NSFW content</div>"}},
                })

                target.text().should.not.match(/This is #NSFW content/)
                target.instance().toggleNsfwShield()
                target.instance().$nextTick(() => {
                    target.text().should.match(/This is #NSFW content/)
                    done()
                })
            })
        })
    })
})
