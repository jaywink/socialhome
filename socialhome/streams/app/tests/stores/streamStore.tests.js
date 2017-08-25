import {Server, WebSocket} from "mock-socket"

import Vuex from "vuex"

import {newinstance, stateOperations} from "streams/app/stores/streamStore"
import {actions, mutations} from "streams/app/stores/streamStore.operations"


describe("streamStore", () => {
    afterEach(() => {
        Sinon.restore()
    })

    describe("newinstance", () => {
        context("when websocket connects", () => {
            it("should connect with protocol wss:// when browser protocol is HTTPS", () => {
                jsdom.reconfigure({url: "https://localhost"})
                window.context = {streamName: "public"}
                const mockWebSocket = Sinon.spy()
                newinstance({WebSocketImpl: mockWebSocket})
                mockWebSocket.getCall(0).args[0].should.equal("wss://localhost/ch/streams/public/")
            })

            it("should connect with protocol ws:// when browser protocol is HTTP", () => {
                jsdom.reconfigure({url: "http://localhost"})
                window.context = {streamName: "public"}
                const mockWebSocket = Sinon.spy()
                newinstance({WebSocketImpl: mockWebSocket})
                mockWebSocket.getCall(0).args[0].should.equal("ws://localhost/ch/streams/public/")
            })
        })

        context("when websocket receives a message", () => {
            it("should dispatch receivedNewContent to store when serveur sends a nex message", (done) => {
                let mockserver = new Server("wss://localhost:8080/ch/streams/public/")
                jsdom.reconfigure({url: "https://localhost:8080"})
                window.context = {streamName: "public"}
                Sinon.spy(Vuex.Store.prototype, "dispatch")
                mockserver.on("connection", () => mockserver.send(JSON.stringify({event: "new", id: 4})))
                newinstance({WebSocketImpl: WebSocket})
                setTimeout(() => {
                    Vuex.Store.prototype.dispatch.getCall(0).args.should.eql([stateOperations.receivedNewContent, 1])
                    done()
                }, 200)
            })
        })
    })

    describe("mutations", () => {
        describe("receivedNewContent", () => {
            it("should set state.stream.hasNewContent to true", () => {
                let state = {hasNewContent: false, newContentLengh: 0, contentList: {}}
                mutations[stateOperations.receivedNewContent](state, 42)
                state.hasNewContent.should.be.true
            })

            it("should increment state.stream.newContentLengh by 1", () => {
                let state = {hasNewContent: false, newContentLengh: 0, contentList: {}}
                mutations[stateOperations.receivedNewContent](state, 42)
                state.newContentLengh.should.equal(1)
            })

            it("should add the new post id to the content list with undefined value", () => {
                let state = {hasNewContent: false, newContentLengh: 0, contentList: {}}
                mutations[stateOperations.receivedNewContent](state, 42)
                state.contentList.should.eql({42: undefined})
            })
        })
        describe("newContentAck", () => {
            it("should set state.stream.hasNewContent to true", () => {
                let state = {hasNewContent: true, newContentLengh: 0}
                mutations[stateOperations.newContentAck](state)
                state.hasNewContent.should.be.false
            })

            it("should set state.stream.newContentLengh to 0", () => {
                let state = {hasNewContent: true, newContentLengh: 10}
                mutations[stateOperations.newContentAck](state)
                state.newContentLengh.should.equal(0)
            })
        })
    })

    describe("actions", () => {
        describe("receivedNewContent", () => {
            it("should commit with the correct parameters", () => {
                let commit = Sinon.spy()
                actions[stateOperations.receivedNewContent]({commit}, 10)
                commit.getCall(0).args.should.eql([stateOperations.receivedNewContent, 10])
            })
        })
        describe("newContentAck", () => {
            it("should commit with the correct parameters", () => {
                let commit = Sinon.spy()
                actions[stateOperations.newContentAck]({commit})
                commit.getCall(0).args[0].should.equal(stateOperations.newContentAck)
            })
        })
    })
})
