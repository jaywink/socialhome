import Axios from "axios"
import moxios from "moxios"
import Vue from "vue"
import {mount} from "avoriaz"

import StreamElementReactionsBar from "streams/app/components/ReactionsBar.vue"
import {getStreamElementReactionsBarPropsData} from "streams/app/tests/fixtures/ReactionsBar.fixtures"


describe("ReactionsBar", () => {
    beforeEach(() => {
        Sinon.restore()
    })

    describe("computed", () => {
        describe("showReplies", () => {
            it("should be true if authenticated or has children", () => {
                let propsData = getStreamElementReactionsBarPropsData({repliesCount: 0})
                let target = new StreamElementReactionsBar({propsData})
                target.$store.state.isUserAuthenticated = true
                target.showReplies.should.be.true

                propsData = getStreamElementReactionsBarPropsData({repliesCount: 1})
                target = new StreamElementReactionsBar({propsData})
                target.$store.state.isUserAuthenticated = false
                target.showReplies.should.be.true

                propsData = getStreamElementReactionsBarPropsData({repliesCount: 0})
                target = new StreamElementReactionsBar({propsData})
                target.$store.state.isUserAuthenticated = false
                target.showReplies.should.be.false
            })
        })

        describe("showShares", () => {
            it("should be true if authenticated or has shares", () => {
                let propsData = getStreamElementReactionsBarPropsData({sharesCount: 0})
                let target = new StreamElementReactionsBar({propsData})
                target.$store.state.isUserAuthenticated = true
                target.showShares.should.be.true

                propsData = getStreamElementReactionsBarPropsData({sharesCount: 1})
                target = new StreamElementReactionsBar({propsData})
                target.$store.state.isUserAuthenticated = false
                target.showShares.should.be.true

                propsData = getStreamElementReactionsBarPropsData({sharesCount: 0})
                target = new StreamElementReactionsBar({propsData})
                target.$store.state.isUserAuthenticated = false
                target.showShares.should.be.false
            })
        })
    })

    describe("methods", () => {
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

        describe("expandShares", () => {
            it("should toggle showSharesBox", () => {
                let propsData = getStreamElementReactionsBarPropsData()
                let target = new StreamElementReactionsBar({propsData})
                target.expandShares()
                target.showSharesBox.should.be.true
                target.expandShares()
                target.showSharesBox.should.be.false
            })
        })

        describe("share", () => {
            it("should show the reshare bow", () => {
                let propsData = getStreamElementReactionsBarPropsData()
                let target = mount(StreamElementReactionsBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = true
                target.instance().$data.showRepliesBox = true

                target.instance().expandShares()
                target.instance().$data.showSharesBox.should.be.true
                target.instance().$data.showRepliesBox.should.be.false
            })

            it("should create share on server", (done) => {
                let propsData = getStreamElementReactionsBarPropsData()
                let target = mount(StreamElementReactionsBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = true
                target.instance().share()

                moxios.wait(() => {
                    let request = moxios.requests.mostRecent()
                    request.respondWith({
                        status: 200,
                        response: {status: "ok", content_id: 123},
                    }).then(() => {
                        target.instance().$data.showSharesBox.should.be.false
                        target.instance().$data.sharesCount$.should.eq(propsData.sharesCount + 1)
                        done()
                    })
                })
            })
        })

        describe("unshare", () => {
            it("should removes share on server", (done) => {
                let propsData = getStreamElementReactionsBarPropsData({hasShared: true})
                let target = mount(StreamElementReactionsBar, {propsData})
                target.instance().$store.state.isUserAuthenticated = true

                // Ensure data
                target.instance().expandShares()
                target.instance().showSharesBox.should.be.true
                target.instance().hasShared$.should.be.true

                // Actual thing we are testing - the unshare
                target.instance().unshare()

                moxios.wait(() => {
                    moxios.requests.mostRecent().respondWith({
                        status: 200,
                        response: {status: "ok"}
                    }).then(() => {
                        target.instance().showSharesBox.should.be.false
                        target.instance().sharesCount$.should.eq(propsData.sharesCount - 1)
                        target.instance().hasShared$.should.be.false
                        done()
                    })
                })
            })
        })
    })
})
