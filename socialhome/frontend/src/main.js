import Vue from "vue"
import ReconnectingWebSocket from "ReconnectingWebSocket/reconnecting-websocket.min"

import initVue from "@/init-vue"
import router from "@/routes"
import store from "@/store"

import "@/styles/index.scss"


initVue(Vue)

const main = new Vue({
    el: "#app",
    store,
    router,
    created() {
        this.$websocket = new ReconnectingWebSocket(this.websocketPath())
        this.$websocket.onmessage = message => this.onWebsocketMessage(message)
    },
    beforeDestroy() {
        this.$websocket.close()
    },
    methods: {
        onWebsocketMessage(message) {
            const data = JSON.parse(message.data)

            if (data.event === "new") {
                this.$store.dispatch("stream/receivedNewContent", data.id)
            }
        },
        websocketPath() {
            const websocketProtocol = window.location.protocol === "https:" ? "wss" : "ws"
            return `${websocketProtocol}://${window.location.host}/ch/streams/${this.$store.state.stream.streamName}/`
        },
    },
})

export default main
