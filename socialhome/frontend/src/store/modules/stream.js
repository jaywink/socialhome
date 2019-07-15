/* eslint-disable no-param-reassign */
import Vue from "vue"
import Vapi from "vuex-rest-api"
import _defaults from "lodash/defaults"

import getState from "@/store/modules/stream.state"
import {streamActions, streamMutations, streamGetters} from "@/store/modules/stream.operations"


export function addHasLoadMore(state) {
    const loadMoreContentId = state.contentIds[state.contentIds.length - 6]
    if (loadMoreContentId) {
        Vue.set(state.contents[loadMoreContentId], "hasLoadMore", true)
    } else {
    // Add to the last to be sure we always add it
        Vue.set(state.contents[state.contentIds[state.contentIds.length - 1]], "hasLoadMore", true)
    }
    state.layoutDoneAfterTwitterOEmbeds = false
}

export function fetchContentsSuccess(state, payload) {
    let newItems = 0
    payload.data.forEach(item => {
        const content = Object.assign({}, item, {replyIds: [], shareIds: []})
        Vue.set(state.contents, content.id, content)
        if (state.contentIds.indexOf(content.id) === -1) {
            state.contentIds.push(content.id)
            newItems += 1
        }
    })
    if (newItems > 0) {
        addHasLoadMore(state)
    }
}

export function fetchRepliesSuccess(state, payload) {
    let items = payload.data
    if (!Array.isArray(payload.data)) {
        items = [payload.data]
    }
    items.forEach(item => {
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

export function fetchSharesSuccess(state, payload) {
    payload.data.forEach(item => {
        const share = Object.assign({}, item, {replyIds: []})
        Vue.set(state.shares, share.id, share)
        if (state.contents[share.share_of].shareIds.indexOf(share.id) === -1) {
            state.contents[share.share_of].shareIds.push(share.id)
        }
    })
}

export function fetchNewContentSuccess(state, payload) {
    Vue.set(state.contents, payload.data.id, payload.data)
}

export function onError() {
    Vue.snotify.error(gettext("An error happened while fetching new content"))
}

export function newRestAPI() {
    const getLastIdParam = lastId => (lastId ? `?last_id=${lastId}` : "")

    const options = {
        baseURL: "",
        axios: Vue.axios,
        state: getState(),
    }

    return new Vapi(options)
        .post({
            action: "followTag",
            path: ({uuid = undefined}) => `${Urls["api:tag-follow"]({uuid})}`,
            onSuccess: () => {},
            onError,
        })
        .get({
            action: "getPublicStream",
            path: ({lastId = undefined}) => `${Urls["api-streams:public"]()}${getLastIdParam(lastId)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getFollowedStream",
            path: ({lastId = undefined}) => `${Urls["api-streams:followed"]()}${getLastIdParam(lastId)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getLimitedStream",
            path: ({lastId = undefined}) => `${Urls["api-streams:limited"]()}${getLastIdParam(lastId)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getLocalStream",
            path: ({lastId = undefined}) => `${Urls["api-streams:local"]()}${getLastIdParam(lastId)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getNewContent",
            path: ({pk}) => Urls["api:content-detail"]({pk}),
            property: "contents",
            onSuccess: fetchNewContentSuccess,
            onError,
        })
        .get({
            action: "getTagStream",
            path: ({name, lastId = undefined}) => `${Urls["api-streams:tag"]({name})}${getLastIdParam(lastId)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getTagsStream",
            path: ({lastId = undefined}) => `${Urls["api-streams:tags"]()}${getLastIdParam(lastId)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getProfileAll",
            path: ({uuid, lastId = undefined}) => `${Urls["api-streams:profile-all"]({uuid})}${getLastIdParam(lastId)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getProfilePinned",
            path: (
                {uuid, lastId = undefined},
            ) => `${Urls["api-streams:profile-pinned"]({uuid})}${getLastIdParam(lastId)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getReplies",
            path: ({id}) => Urls["api:content-replies"]({pk: id}),
            property: "replies",
            onSuccess: fetchRepliesSuccess,
            onError,
        })
        .get({
            action: "getShares",
            path: ({id}) => Urls["api:content-shares"]({pk: id}),
            property: "shares",
            onSuccess: fetchSharesSuccess,
            onError,
        })
        .post({
            action: "saveReply",
            path: Urls["api:content-list"],
            property: "reply",
            onSuccess: fetchRepliesSuccess,
            onError,
        })
        .post({
            action: "unfollowTag",
            path: ({uuid = undefined}) => `${Urls["api:tag-unfollow"]({uuid})}`,
            onSuccess: () => {},
            onError,
        })
        .getStore()
}

const streamsAPI = newRestAPI()

const {state} = streamsAPI

export const getters = _defaults({}, streamGetters, streamsAPI.getters)

export const actions = _defaults({}, streamActions, streamsAPI.actions)

export const mutations = _defaults({}, streamMutations, streamsAPI.mutations)

export default {
    namespaced: true,
    state,
    getters,
    actions,
    mutations,
}
