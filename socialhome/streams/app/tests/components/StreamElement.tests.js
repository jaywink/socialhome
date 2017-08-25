import Axios from "axios"
import moxios from "moxios"
import Vue from "vue"
import {mount} from "avoriaz"

import StreamElement from "streams/app/components/StreamElement.vue"
import {getStreamElementPropsData} from "streams/app/tests/fixtures/StreamElement.fixtures";


describe("StreamElement", () => {
    beforeEach(() => {
        Sinon.restore()
    })

    describe("template", () => {
        describe("share reaction", () => {
            it("has item-reaction-shared if has shared", () => {
                let propsData = getStreamElementPropsData({hasShared: false})
                let target = mount(StreamElement, {propsData})
                target.find(".item-reaction.item-reaction-shared").length.should.eq(0)

                propsData = getStreamElementPropsData({hasShared: true})
                target = mount(StreamElement, {propsData})
                target.find(".item-reaction.item-reaction-shared").length.should.eq(1)
            })
        })
    })

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

        describe("getSharesCount", () => {
            it("returns share count", () => {
                let propsData = getStreamElementPropsData({sharesCount: 56})
                let target = new StreamElement({propsData})
                target.getSharesCount.should.eq(56)
            })
        })

        describe("getHasShared", () => {
            it("returns has shared status", () => {
                let propsData = getStreamElementPropsData({hasShared: false})
                let target = new StreamElement({propsData})
                target.getHasShared.should.be.false

                propsData = getStreamElementPropsData({hasShared: true})
                target = new StreamElement({propsData})
                target.getHasShared.should.be.true

                target.$data._hasShared = false
                target.getHasShared.should.be.false

                target.$data._hasShared = true
                target.getHasShared.should.be.true
            })
        })
    })

    describe("methods", () => {
        describe("expandShares", () => {
            it("toggles showSharesBox", () => {
                let propsData = getStreamElementPropsData()
                let target = new StreamElement({propsData})
                target.expandShares()
                target.showSharesBox.should.be.true
                target.expandShares()
                target.showSharesBox.should.be.false
            })
        })

        describe("share", () => {
            beforeEach(() => {
                Vue.prototype.$http = Axios.create({
                    xsrfCookieName: "csrftoken",
                    xsrfHeaderName: "X-CSRFToken",
                })
                moxios.install(Vue.prototype.$http)
            })

            afterEach(() => {
                moxios.uninstall()
            })

            it("creates share on server", (done) => {
                let propsData = getStreamElementPropsData({isUserAuthenticated: true, hasShared: false})
                let target = mount(StreamElement, {propsData})
                // Ensure data
                target.instance().expandShares()
                target.instance().$data.showSharesBox.should.be.true
                target.instance().$data._hasShared.should.be.false

                // Actual thing we are testing - the share
                target.instance().share()

                moxios.wait(() => {
                    let request = moxios.requests.mostRecent()
                    request.respondWith({
                        status: 200,
                        response: {
                            status: "ok", content_id: 123,
                        }
                    }).then(() => {
                        target.instance().$data.showSharesBox.should.be.false
                        target.instance().$data._sharesCount.should.eq(propsData.sharesCount + 1)
                        target.instance().$data._hasShared.should.be.true
                        done()
                    })
                })
            })
        })

        describe("unshare", () => {
            beforeEach(() => {
                Vue.prototype.$http = Axios.create({
                    xsrfCookieName: "csrftoken",
                    xsrfHeaderName: "X-CSRFToken",
                })
                moxios.install(Vue.prototype.$http)
            })

            afterEach(() => {
                moxios.uninstall()
            })

            it("removes share on server", (done) => {
                let propsData = getStreamElementPropsData({isUserAuthenticated: true, hasShared: true})
                let target = mount(StreamElement, {propsData})
                // Ensure data
                target.instance().expandShares()
                target.instance().$data.showSharesBox.should.be.true
                target.instance().$data._hasShared.should.be.true

                // Actual thing we are testing - the unshare
                target.instance().unshare()

                moxios.wait(() => {
                    let request = moxios.requests.mostRecent()
                    request.respondWith({
                        status: 200,
                        response: {status: "ok"},
                    }).then(() => {
                        target.instance().$data.showSharesBox.should.be.false
                        target.instance().$data._sharesCount.should.eq(propsData.sharesCount - 1)
                        target.instance().$data._hasShared.should.be.false
                        done()
                    })
                })
            })
        })
    })
})
