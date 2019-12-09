import Vue from "vue"

import main from "@/main"


describe("Main", () => {
    beforeEach(() => {
        Sinon.restore()
    })

    it("should initialize Axios library with correct parameters", () => {
        Vue.prototype.$http.should.exist
        Vue.prototype.$http.defaults.xsrfCookieName.should.equal("csrftoken")
        Vue.prototype.$http.defaults.xsrfHeaderName.should.equal("X-CSRFToken")
    })

    it("VueMasonry is correctly initialized is defined", () => {
        Vue.prototype.$redrawVueMasonry.should.be.a("function")
        main.$redrawVueMasonry.should.be.a("function")
    })

    describe("`main` instance", () => {
        describe("methods", () => {
            describe("onWebsocketMessage", () => {
                it("should dispatch receivedNewContent to store when serveur sends a next message", () => {
                    Sinon.spy(main.$store, "dispatch")
                    main.onWebsocketMessage({
                        data: JSON.stringify({
                            event: "new", id: 4,
                        }),
                    })
                    main.$store.dispatch.getCall(0).args
                        .should.eql(["stream/receivedNewContent", 4])
                })
            })

            describe("websocketPath", () => {
                it("should connect with protocol wss:// when browser protocol is HTTPS", () => {
                    jsdom.reconfigure({url: "https://localhost"})
                    main.$store.state.stream.streamName = "public"

                    main.websocketPath().should.eq("wss://localhost/ch/streams/public/")
                })

                it("should connect with protocol ws:// when browser protocol is HTTP", () => {
                    jsdom.reconfigure({url: "http://localhost"})
                    main.$store.state.stream.streamName = "public"

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
                const msg = {
                    data: JSON.stringify({
                        event: "new", id: 4,
                    }),
                }
                main.$websocket.onmessage(msg)
                main.onWebsocketMessage.getCall(0).args.should.eql([{
                    data: JSON.stringify({
                        event: "new", id: 4,
                    }),
                }])
            })

            it("should initialize `Vue.snotify`", () => {
                Vue.snotify.should.exist
            })
        })

        describe("beforeDestroy", () => {
            it("should call `main.$websocket.close`", () => {
                const spy = Sinon.spy(main.$websocket, "close")
                main.$destroy()
                spy.called.should.be.true
            })
        })
    })
})
