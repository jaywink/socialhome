import main from "streams/app/main"

import Vue from "vue"
import Vuex from "vuex"
import {streamStoreOperations} from "../stores/streamStore"


describe("Main", () => {
    beforeEach(() => {
        Sinon.restore()
    })

    it("should initialize Axios library with correct parameters", () => {
        Vue.prototype.$http.should.exist
        Vue.prototype.$http.defaults.xsrfCookieName.should.equal("csrftoken")
        Vue.prototype.$http.defaults.xsrfHeaderName.should.equal("X-CSRFToken")
    })

    it("Vue.redrawVueMasonry is defined", () => {
        (typeof Vue.redrawVueMasonry).should.equal("function")
    })

    describe("`main` instance", () => {
        describe("methods", () => {
            describe("onWebsocketMessage", () => {
                it("should dispatch receivedNewContent to store when serveur sends a next message", () => {
                    Sinon.spy(main.$store, "dispatch")
                    main.onWebsocketMessage({data: JSON.stringify({event: "new", id: 4})})
                    main.$store.dispatch.getCall(0).args
                        .should.eql([streamStoreOperations.receivedNewContent, 4])
                })
            })

            describe("websocketPath", () => {
                it("should connect with protocol wss:// when browser protocol is HTTPS", () => {
                    jsdom.reconfigure({url: "https://localhost"})
                    main.$store.state.streamName = "public"

                    main.websocketPath().should.eq("wss://localhost/ch/streams/public/")
                })

                it("should connect with protocol ws:// when browser protocol is HTTP", () => {
                    jsdom.reconfigure({url: "http://localhost"})
                    main.$store.state.streamName = "public"

                    main.websocketPath().should.eq("ws://localhost/ch/streams/public/")
                })
            })
        })
    })
    describe("Lifecycle", () => {
        describe("created", () => {
            it("should initialize `main.$websocket`", () => {
                main.$websocket.should.exist
            })

            it("should initialize `main.$websocket.onmessage`", () => {
                Sinon.spy(main, "onWebsocketMessage")
                let msg = {data: JSON.stringify({event: "new", id: 4})}
                main.$websocket.onmessage(msg)
                main.onWebsocketMessage.getCall(0).args.should.eql([{data: JSON.stringify({event: "new", id: 4})}])
            })
        })

        describe("beforeDestroy", () => {
            it("should call `main.$websocket.close`", () => {
                let spy = Sinon.spy(main.$websocket, "close")
                main.$destroy()
                spy.called.should.be.true
            })
        })
    })
})
