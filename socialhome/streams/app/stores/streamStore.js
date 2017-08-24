import Vue from "vue"
import Vuex from "vuex"
import ReconnectingWebSocket from "reconnecting-websocket"

import getState from "streams/app/stores/streamStore.state"
import {actions, mutations, stateOperations} from "streams/app/stores/streamStore.operations"


Vue.use(Vuex)

function newinstance(WebSocketImpl = ReconnectingWebSocket) {
    const state = getState()
    const store = new Vuex.Store({state, mutations, actions})
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws"
    const wsPath = `${wsProtocol}://${window.location.host}/ch/streams/${state.stream.streamName}/`
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

const store = newinstance()

export default store
export {store, stateOperations, newinstance}
