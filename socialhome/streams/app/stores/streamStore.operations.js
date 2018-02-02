/* eslint-disable no-param-reassign */
import Vue from "vue"
import _concat from "lodash/concat"
import _difference from "lodash/difference"


const streamStoreOperations = {
    disableLoadMore: "disableLoadMore",
    getFollowedStream: "getFollowedStream",
    getNewContent: "getNewContent",
    getProfileAll: "getProfileAll",
    getProfilePinned: "getProfilePinned",
    getPublicStream: "getPublicStream",
    getReplies: "getReplies",
    getShares: "getShares",
    getTagStream: "getTagStream",
    loadStream: "loadStream",
    newContentAck: "newContentAck",
    receivedNewContent: "receivedNewContent",
    saveReply: "saveReply",
    setLayoutDoneAfterTwitterOEmbeds: "setLayoutDoneAfterTwitterOEmbeds",
}

const mutations = {
    [streamStoreOperations.disableLoadMore](state, contentId) {
        Vue.set(state.contents[contentId], "hasLoadMore", false)
    },
    [streamStoreOperations.receivedNewContent](state, contentId) {
        state.unfetchedContentIds.push(contentId)
    },
    [streamStoreOperations.setLayoutDoneAfterTwitterOEmbeds](state, status) {
        state.layoutDoneAfterTwitterOEmbeds = status
    },
    [streamStoreOperations.newContentAck](state) {
        /*
         * First, get all IDs present in unfetchedContentIds and absent in contentIds
         * This is neccessary since content ids that could not be fetched due to
         * network errors are not removed from `state.unfetchedContentIds`. In this
         * case, the next time unfetched content is fetched, these ids would be added
         * twice and appear twice in the stream.
         */
        const diff = _difference(state.unfetchedContentIds, state.contentIds)
        Vue.set(state, "contentIds", _concat(diff, state.contentIds))
        state.unfetchedContentIds.length = 0
    },
}

const actions = {
    [streamStoreOperations.disableLoadMore]({commit}, contentId) {
        commit(streamStoreOperations.disableLoadMore, contentId)
    },
    [streamStoreOperations.loadStream]({dispatch, state}) {
        const options = {params: {}}
        const lastContentId = state.contentIds[state.contentIds.length - 1]
        if (lastContentId && state.contents[lastContentId]) {
            options.params.lastId = state.contents[lastContentId].through
        }

        switch (state.stream.name) {
            case "followed":
                dispatch(streamStoreOperations.getFollowedStream, options)
                break
            case "public":
                dispatch(streamStoreOperations.getPublicStream, options)
                break
            case "tag":
                options.params.name = state.tagName
                dispatch(streamStoreOperations.getTagStream, options)
                break
            case "profile_all":
                options.params.id = state.applicationStore.profile.id
                dispatch(streamStoreOperations.getProfileAll, options)
                break
            case "profile_pinned":
                options.params.id = state.applicationStore.profile.id
                dispatch(streamStoreOperations.getProfilePinned, options)
                break
            default:
                console.log(`Unknown stream name ${state.stream.name}`)
        }
    },
    [streamStoreOperations.receivedNewContent]({commit}, newContentLengh) {
        commit(streamStoreOperations.receivedNewContent, newContentLengh)
    },
    [streamStoreOperations.setLayoutDoneAfterTwitterOEmbeds]({commit}, status) {
        commit(streamStoreOperations.setLayoutDoneAfterTwitterOEmbeds, status)
    },
    [streamStoreOperations.newContentAck]({commit, dispatch, state}) {
        const promises = []
        const unfetchedContentIds = _concat([], state.unfetchedContentIds)

        commit(streamStoreOperations.newContentAck)

        unfetchedContentIds.forEach(pk => {
            // Force the promise to resolve in all cases
            const reAddAndResolve = () => {
                state.unfetchedContentIds.push(pk)
                return Promise.resolve()
            }
            const promise = dispatch(streamStoreOperations.getNewContent, {params: {pk}})
                .then(Promise.resolve(), reAddAndResolve)
            promises.push(promise)
        })
        return Promise.all(promises)
    },
}

const getters = {
    contentList(state) {
        const contents = []
        state.contentIds.forEach(id => {
            if (state.contents[id] !== undefined) {
                contents.push(state.contents[id])
            }
        })
        return contents
    },
    replies: state => content => {
        const replies = []
        if (content.content_type === "content") {
            state.contents[content.id].replyIds.forEach(id => {
                replies.push(state.replies[id])
            })
        } else if (content.content_type === "share") {
            state.shares[content.id].replyIds.forEach(id => {
                replies.push(state.replies[id])
            })
        }
        return replies
    },
    shares: state => contentId => {
        const shares = []
        state.contents[contentId].shareIds.forEach(id => {
            shares.push(state.shares[id])
        })
        return shares
    },
    singleContent(state) {
        if (!state.singleContentId) {
            return null
        }
        return state.contents[state.singleContentId]
    },
    hasNewContent(state) {
        return state.unfetchedContentIds.length > 0 && !state.pending.contents
    },
}

export {actions, mutations, streamStoreOperations, getters}
