import Vue from "vue"
import Vuex from "vuex"
import Vapi from "vuex-rest-api"
import ReconnectingWebSocket from "reconnecting-websocket"
import _defaults from "lodash/defaults"
import _get from "lodash/get"

import getState from "streams/app/stores/streamStore.state"
import {actions, mutations, streamStoreOperations, getters} from "streams/app/stores/streamStore.operations"


Vue.use(Vuex)

function addHasLoadMore(state) {
    const loadMoreContentId = state.contentIds[state.contentIds.length - 6]
    if (loadMoreContentId) {
        Vue.set(state.contents[loadMoreContentId], "hasLoadMore", true)
    }
}

function fetchContentsSuccess(state, payload) {
    payload.data.forEach(item => {
        const content = Object.assign({}, item, {replyIds: [], shareIds: []})
        Vue.set(state.contents, content.id, content)
        if (state.contentIds.indexOf(content.id) === -1) {
            state.contentIds.push(content.id)
        }
    })
    if (payload.data.length) {
        addHasLoadMore(state)
    }
}

function fetchRepliesSuccess(state, payload) {
    payload.data.forEach(item => {
        const reply = Object.assign({}, item, {replyIds: [], shareIds: []})
        Vue.set(state.replies, reply.id, reply)
        if (state.contents[reply.parent] !== undefined) {
            if (state.contents[reply.parent].replyIds.indexOf(reply.id) === -1) {
                state.contents[reply.parent].replyIds.push(reply.id)
            }
        } else if (state.shares[reply.parent] !== undefined) {
            if (state.shares[reply.parent].replyIds.indexOf(reply.id) === -1) {
                state.shares[reply.parent].replyIds.push(reply.id)
            }
        }
    })
}

function fetchSharesSuccess(state, payload) {
    payload.data.forEach(item => {
        const share = Object.assign({}, item, {replyIds: []})
        Vue.set(state.shares, share.id, share)
        if (state.contents[share.share_of].shareIds.indexOf(share.id) === -1) {
            state.contents[share.share_of].shareIds.push(share.id)
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
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: streamStoreOperations.getFollowedStream,
            path: Urls["api-streams:followed"](),
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: streamStoreOperations.getTagStream,
            path: ({name}) => Urls["api-streams:tag"]({name}),
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: streamStoreOperations.getProfileAll,
            path: ({id}) => Urls["api-streams:profile-all"]({id}),
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: streamStoreOperations.getProfilePinned,
            path: ({id}) => Urls["api-streams:profile-pinned"]({id}),
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: streamStoreOperations.getReplies,
            path: ({id}) => Urls["api:content-replies"]({pk: id}),
            property: "replies",
            onSuccess: fetchRepliesSuccess,
            onError,
        })
        .get({
            action: streamStoreOperations.getShares,
            path: ({id}) => Urls["api:content-shares"]({pk: id}),
            property: "shares",
            onSuccess: fetchSharesSuccess,
            onError,
        })
        .getStore()
}

function getStructure(state, options) {
    const result = newRestAPI({state})

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

const exportsForTests = {
    getStructure, onError, fetchContentsSuccess, fetchRepliesSuccess, fetchSharesSuccess, newRestAPI,
}
export {streamStoreOperations, newStreamStore, exportsForTests}
