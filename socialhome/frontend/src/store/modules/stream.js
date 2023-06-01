/* eslint-disable no-param-reassign,max-len */
import Vue from "vue"
import Vapi from "vuex-rest-api"
import _defaults from "lodash/defaults"
import _get from "lodash/get"

import Axios from "axios"
import getState from "@/store/modules/stream.state"
import {streamActions, streamGetters, streamMutations} from "@/store/modules/stream.operations"

export function addHasLoadMore(state) {
    const loadMoreContentId = state.currentContentIds[state.currentContentIds.length - 6]
    if (loadMoreContentId) {
        Vue.set(state.contents[loadMoreContentId], "hasLoadMore", true)
    } else {
        // Add to the last to be sure we always add it
        Vue.set(state.contents[state.currentContentIds[state.currentContentIds.length - 1]], "hasLoadMore", true)
    }
    state.layoutDoneAfterTwitterOEmbeds = false
}

export function fetchContentsSuccess(state, payload) {
    let newItems = 0
    payload.data.forEach(item => {
        const content = {
            ...item, replyIds: [], shareIds: [],
        }
        Vue.set(state.contents, content.id, content)
        if (state.currentContentIds.indexOf(content.id) === -1) {
            state.currentContentIds.push(content.id)
            newItems += 1
        }
        if (state.allContentIds.indexOf(content.id) === -1) {
            state.allContentIds.push(content.id)
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
        const reply = {
            ...item, replyIds: [], shareIds: [],
        }
        Vue.set(state.contents, reply.id, reply)
        if (state.contents[reply.parent] !== undefined) {
            if (state.contents[reply.parent].replyIds.indexOf(reply.id) === -1) {
                state.contents[reply.parent].replyIds.push(reply.id)
            }
        }
        if (state.allContentIds.indexOf(reply.id) === -1) {
            state.allContentIds.push(reply.id)
        }
    })
    if (items.length > 0) {
        state.contents[items[0].parent].reply_count = state.contents[items[0].parent].replyIds.length
    }
}

export function fetchSharesSuccess(state, payload) {
    payload.data.forEach(item => {
        const share = {
            ...item, replyIds: [],
        }
        Vue.set(state.contents, share.id, share)
        if (state.contents[share.share_of].shareIds.indexOf(share.id) === -1) {
            state.contents[share.share_of].shareIds.push(share.id)
        }
        if (state.allContentIds.indexOf(share.id) === -1) {
            state.allContentIds.push(share.id)
        }
    })
}

export function fetchNewContentSuccess(state, payload) {
    Vue.set(state.contents, payload.data.id, payload.data)
    if (state.allContentIds.indexOf(payload.data.id) === -1) {
        state.allContentIds.push(payload.data.id)
    }
}

export function onError() {
    Vue.snotify.error(gettext("An error happened while fetching new content"))
}

function shareContentError() {
    Vue.snotify.error(gettext("An error happened while sharing the content"))
}

function shareContentSuccess(state, payload, axios, {params}) {
    // TODO: we should just fetch the share instead and refetch the content?
    Vue.set(state.contents[params.id], "shares_count", state.contents[params.id].shares_count + 1)
    Vue.set(state.contents[params.id], "user_has_shared", true)
}

function unshareContentError() {
    Vue.snotify.error(gettext("An error happened while unsharing the content"))
}

function unshareContentSuccess(state, payload, axios, {params}) {
    // TODO: we should just delete the share instead and refetch the content?
    Vue.set(state.contents[params.id], "shares_count", state.contents[params.id].shares_count - 1)
    Vue.set(state.contents[params.id], "user_has_shared", false)
}

export const profilesPlugin = store => {
    // called when the store is initialized
    store.subscribe(({type, payload}) => {
        if (/^stream\/GET[A-Z_]*SUCCEEDED$/.test(type)) {
            store.commit("profiles/setProfilesFromContentList", payload.payload.data, {root: true})
        } else if (/^stream\/GET_PROFILE_(ALL|PINNED)$/.test(type)) {
            store.commit("profiles/setProfile", _get(window, ["context", "profile"]), {root: true})
        }
    })
}

export function newRestAPI() {
    const getLastIdParam = lastId => (lastId ? `?last_id=${lastId}` : "")
    const getAcceptIdsParam = acceptIds => (acceptIds ? `?accept_ids=${acceptIds.toString()}` : "")

    const axios = Axios.create({
        xsrfCookieName: "csrftoken",
        xsrfHeaderName: "X-CSRFToken",
    })

    const options = {
        baseURL: "",
        axios,
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
            path: ({lastId = undefined, acceptIds = undefined}) => `${Urls["api-streams:public"]()}${getLastIdParam(
                lastId,
            )}${getAcceptIdsParam(acceptIds)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getFollowedStream",
            path: ({lastId = undefined, acceptIds = undefined}) => `${Urls["api-streams:followed"]()}${getLastIdParam(
                lastId,
            )}${getAcceptIdsParam(acceptIds)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getLimitedStream",
            path: ({lastId = undefined, acceptIds = undefined}) => `${Urls["api-streams:limited"]()}${getLastIdParam(
                lastId,
            )}${getAcceptIdsParam(acceptIds)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getLocalStream",
            path: ({lastId = undefined, acceptIds = undefined}) => `${Urls["api-streams:local"]()}${getLastIdParam(
                lastId,
            )}${getAcceptIdsParam(acceptIds)}`,
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
            path: ({name, lastId = undefined, acceptIds = undefined}) => `${Urls["api-streams:tag"](
                {name},
            )}${getLastIdParam(lastId)}${getAcceptIdsParam(acceptIds)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getTagsStream",
            path: ({lastId = undefined, acceptIds = undefined}) => `${Urls["api-streams:tags"]()}${getLastIdParam(
                lastId,
            )}${getAcceptIdsParam(acceptIds)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getProfileAll",
            path: ({uuid, lastId = undefined, acceptIds = undefined}) => `${Urls["api-streams:profile-all"](
                {uuid},
            )}${getLastIdParam(lastId)}${getAcceptIdsParam(acceptIds)}`,
            property: "contents",
            onSuccess: fetchContentsSuccess,
            onError,
        })
        .get({
            action: "getProfilePinned",
            path: (
                {uuid, lastId = undefined, acceptIds = undefined},
            ) => `${Urls["api-streams:profile-pinned"]({uuid})}${getLastIdParam(lastId)}${getAcceptIdsParam(
                acceptIds,
            )}`,
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
            action: "shareContent",
            path: ({id}) => Urls["api:content-share"]({pk: id}),
            onSuccess: shareContentSuccess,
            onError: shareContentError,
        })
        .post({
            action: "unfollowTag",
            path: ({uuid = undefined}) => `${Urls["api:tag-unfollow"]({uuid})}`,
            onSuccess: () => {},
            onError,
        })
        .delete({
            action: "unshareContent",
            path: ({id}) => Urls["api:content-share"]({pk: id}),
            onSuccess: unshareContentSuccess,
            onError: unshareContentError,
        })
        .getStore()
}

const streamsAPI = newRestAPI()
const {state} = streamsAPI
const getters = _defaults({}, streamGetters, streamsAPI.getters)
const actions = _defaults({}, streamActions, streamsAPI.actions)
const mutations = _defaults({}, streamMutations, streamsAPI.mutations)

function getStreamStore() {
    const store = newRestAPI()
    return {
        namespaced: true,
        state: store.state,
        getters,
        actions,
        mutations,
    }
}

export default {
    namespaced: true,
    state,
    getters,
    actions,
    mutations,
}

export {
    getStreamStore,
    getters,
    actions,
    mutations,
}
