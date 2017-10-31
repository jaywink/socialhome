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
        Vue.set(state.replyIds, item.id, [])
        Vue.set(state.shareIds, item.id, [])
        if (item.content_type === "content") {
            state.contentIds.push(item.id)
        } else if (item.content_type === "reply") {
            if (state.replyIds[item.parent] === undefined) {
                Vue.state(state.replyIds, item.parent, [item.id])
            } else if (!state.replyIds[item.parent].includes(item.id)) {
                state.replyIds[item.parent].push(item.id)
            }
        } else if (item.content_type === "share") {
            if (state.shareIds[item.share_of] === undefined) {
                Vue.set(state.shareIds, item.share_of, [item.id])
            } else if (!state.shareIds[item.share_of].includes(item.id)) {
                state.shareIds[item.share_of].push(item.id)
            }
        }
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
            action: streamStoreOperations.getProfileAll,
            path: ({id}) => Urls["api-streams:profile-all"]({id}),
            property: "contents",
            onSuccess: options.onSuccess,
            onError: options.onError,
        })
        .get({
            action: streamStoreOperations.getProfilePinned,
            path: ({id}) => Urls["api-streams:profile-pinned"]({id}),
            property: "contents",
            onSuccess: options.onSuccess,
            onError: options.onError,
        })
        .get({
            action: streamStoreOperations.getReplies,
            path: ({ id }) => Urls["api:content-replies"]({ pk: id }),
            property: "contents",
            onSuccess: options.onSuccess,
            onError: options.onError,
        })
        .get({
            action: streamStoreOperations.getShares,
            path: ({ id }) => Urls["api:content-shares"]({ pk: id }),
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
