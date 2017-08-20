import "chai/register-should"

import StreamElement from "streams/app/components/StreamElement.vue"
import {getStreamElementPropsData} from "../fixtures/StreamElement.fixtures";


describe("StreamElement", () => {
    describe("computed", () => {
        describe("showReplies", () => {
            it("true if authenticated or has children", () => {
                let propsData = getStreamElementPropsData({isUserAuthenticated: true, childrenCount: 0})
                let target = new StreamElement({propsData})
                target.showReplies.should.be.true

                propsData = getStreamElementPropsData({isUserAuthenticated: false, childrenCount: 1})
                target = new StreamElement({propsData})
                target.showReplies.should.be.true

                propsData = getStreamElementPropsData({isUserAuthenticated: false, childrenCount: 0})
                target = new StreamElement({propsData})
                target.showReplies.should.be.false
            })
        })

        describe("showShares", () => {
            it("true if authenticated or has shares", () => {
                let propsData = getStreamElementPropsData({isUserAuthenticated: true, sharesCount: 0})
                let target = new StreamElement({propsData})
                target.showShares.should.be.true

                propsData = getStreamElementPropsData({isUserAuthenticated: false, sharesCount: 1})
                target = new StreamElement({propsData})
                target.showShares.should.be.true

                propsData = getStreamElementPropsData({isUserAuthenticated: false, sharesCount: 0})
                target = new StreamElement({propsData})
                target.showShares.should.be.false
            })
        })
    })
})
