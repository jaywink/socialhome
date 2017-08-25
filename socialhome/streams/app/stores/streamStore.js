import Vue from "vue"
import Vuex from "vuex"
import ReconnectingWebSocket from "reconnecting-websocket"
import _defaults from "lodash/defaults"
import _get from "lodash/get"

import getState from "streams/app/stores/streamStore.state"
import {actions, mutations, stateOperations} from "streams/app/stores/streamStore.operations"


Vue.use(Vuex)

function newinstance(options) {
    const state = getState()
    const opts = _defaults({}, {state, mutations, actions}, options)
    const WebSocketImpl = _get(opts, ["WebSocketImpl"], ReconnectingWebSocket)
    delete opts.WebSocketImpl

    const store = new Vuex.Store(opts)
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws"
    const wsPath = `${wsProtocol}://${window.location.host}/ch/streams/${state.streamName}/`
    const ws = new WebSocketImpl(wsPath)

    ws.onmessage = message => {
        const data = JSON.parse(message.data)

        if (data.event === "new") {
            store.dispatch(stateOperations.receivedNewContent, 1)
        }
    }

    store.$websocket = ws

    return store
}

export {stateOperations, newinstance}
