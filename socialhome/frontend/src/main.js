import Vue from "vue"
import ReconnectingWebSocket from "ReconnectingWebSocket/reconnecting-websocket.min"
import _isString from "lodash/isString"
import _get from "lodash/get"
import _isFunction from "lodash/isFunction"

import initVue from "@/init-vue"
import router from "@/routes"
import getStore from "@/store"

import "@/styles/index.scss"

function getMainInstance(LocalVue) {
    initVue(LocalVue)

    return new LocalVue({
        el: "#app",
        store: getStore(LocalVue),
        router,
        data() {
            return {pingTimer: null}
        },
        created() {
            const wsPath = this.websocketPath()
            if (_isString(wsPath)) {
                this.$websocket = new ReconnectingWebSocket(wsPath)
                this.$websocket.onmessage = message => this.onWebsocketMessage(message)
                this.$websocket.onopen = event => this.onWebsocketOpen(event)
                this.$websocket.onclose = event => this.onWebsocketClose(event)
            } else {
                this.$websocket = undefined
            }
        },
        beforeDestroy() {
            const close = _get(this.$websocket, "close")
            if (_isFunction(close)) close()
        },
        methods: {
            onWebsocketClose() {
                if (this.pingTimer) {
                    clearInterval(this.pingTimer)
                    this.pingTimer = null
                }
            },
            onWebsocketMessage(message) {
                const data = JSON.parse(message.data)

                if (data.event === "new") {
                    this.$store.dispatch("stream/receivedNewContent", {
                        contentId: data.id,
                        parentId: data.parentId,
                    })
                } else if (data.event === "profile") {
                    this.$store.dispatch("profiles/getProfile", {uuid: data.uuid})
                }
            },
            onWebsocketOpen() {
                this.pingTimer = setInterval(() => {
                    this.$websocket.send(JSON.stringify({event: "ping"}))
                }, 60000)
            },
            websocketPath() {
                const streamName = _get(this.$store, ["state", "stream", "streamName"])
                if (_isString(streamName) && streamName.length > 0) {
                    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws"
                    return `${wsProtocol}://${window.location.host}/ch/streams/${streamName}/`
                }
                return undefined
            },
        },
    })
}

const main = getMainInstance(Vue)

export default main
export {main, getMainInstance}
