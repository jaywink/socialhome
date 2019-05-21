import Vue from "vue"
import BootstrapVue from "bootstrap-vue/dist/bootstrap-vue.esm"
import VueInfiniteScroll from "vue-infinite-scroll"
import {VueMasonryPlugin} from "vue-masonry"
import VueRouter from "vue-router"
import VueSnotify from "vue-snotify"
import ReconnectingWebSocket from "ReconnectingWebSocket/reconnecting-websocket.min"

import filters from "@/filters"
import router from "@/routes"
import store from "@/store"

Vue.use(BootstrapVue)
Vue.use(VueInfiniteScroll)
Vue.use(VueMasonryPlugin)
Vue.use(VueRouter)
Vue.use(VueSnotify)

// Globally add filters
Object.entries(filters).forEach(([key, value]) => Vue.filter(`${key}`, value))

const main = new Vue({
    el: "#app",
    store,
    router,
    created() {
        this.$websocket = new ReconnectingWebSocket(this.websocketPath())
        this.$websocket.onmessage = message => this.onWebsocketMessage(message)
        Vue.snotify = this.$snotify
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
