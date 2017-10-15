import Vue from "vue"
import Vuex from "vuex"
import Vapi from "vuex-rest-api"
import ReconnectingWebSocket from "reconnecting-websocket"
import _defaults from "lodash/defaults"
import _get from "lodash/get"

import getState from "streams/app/stores/streamStore.state"
import {actions, mutations, streamStoreOperations, getters} from "streams/app/stores/streamStore.operations"

Vue.use(Vuex)

function onSuccess(state, payload) {
    payload.data.forEach(item => {
        Vue.set(state.contents, item.id, item)
        state.contentIds.push(item.id)
    })
}

function onError(state, error) {
    /* TODO: Proper error handling */
    console.error(`An error happened while fetching post: ${error}`)
}

function newRestAPI(options) {
    const opts = _defaults({}, options, {
        baseURL: "",
        axios: Vue.prototype.$http,
    })

    return new Vapi(opts)
        .get({
            action: streamStoreOperations.getPublicStream,
            path: Urls["api-streams:public"](),
            property: "contents",
            onSuccess: options.onSuccess,
            onError: options.onError,
        })
        .get({
            action: streamStoreOperations.getFollowedStream,
            path: Urls["api-streams:followed"](),
            property: "contents",
            onSuccess: options.onSuccess,
            onError: options.onError,
        })
        .get({
            action: streamStoreOperations.getTagStream,
            path: ({name}) => Urls["api-streams:tag"]({name}),
            property: "contents",
            onSuccess: options.onSuccess,
            onError: options.onError,
        })
        .get({
            action: streamStoreOperations.getProfileStream,
            path: ({guid}) => Urls["api:streams-profile-all"]({guid}),
            property: "contents",
            onSuccess: options.onSuccess,
            onError: options.onError,
        })
        .getStore()
}

function getStructure(state, options) {
    const result = newRestAPI({state, onError, onSuccess})

    result.mutations = _defaults({}, mutations, result.mutations)
    result.actions = _defaults({}, actions, result.actions)
    result.getters = _defaults({}, getters, result.getters)

    return _defaults({}, result, options)
}

function newStreamStore(options = {}) {
    const state = getState()
    const opts = _defaults({}, options)

    // This exists for test puposes
    const WebSocketImpl = _get(opts, ["WebSocketImpl"], ReconnectingWebSocket)
    delete opts.WebSocketImpl

    const store = new Vuex.Store(getStructure(state, opts))

    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws"
    const wsPath = `${wsProtocol}://${window.location.host}/ch/streams/${state.streamName}/`
    const ws = new WebSocketImpl(wsPath)

    ws.onmessage = message => {
        const data = JSON.parse(message.data)

        if (data.event === "new") {
            store.dispatch(streamStoreOperations.receivedNewContent, 1)
        }
    }

    store.$websocket = ws

    return store
}

const exportsForTests = {getStructure, onError, onSuccess, newRestAPI}
export {streamStoreOperations, newStreamStore, exportsForTests}
