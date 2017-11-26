import Vue from "vue"


const streamStoreOperations = {
    disableLoadMore: "disableLoadMore",
    getFollowedStream: "getFollowedStream",
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
}

// This is the Vuex way
/* eslint-disable no-param-reassign */
const mutations = {
    [streamStoreOperations.disableLoadMore](state, contentId) {
        Vue.set(state.contents[contentId], "hasLoadMore", false)
    },
    [streamStoreOperations.receivedNewContent](state, contentId) {
        state.hasNewContent = true
        state.newContentLengh += 1
        state.contentIds.unshift(contentId)
        Vue.set(state.contents, contentId, undefined)
    },
    [streamStoreOperations.newContentAck](state) {
        state.hasNewContent = false
        state.newContentLengh = 0
    },
}
/* eslint-enable no-param-reassign */

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

        if (state.streamName.match(/^followed/)) {
            dispatch(streamStoreOperations.getFollowedStream, options)
        } else if (state.streamName.match(/^public/)) {
            dispatch(streamStoreOperations.getPublicStream, options)
        } else if (state.streamName.match(/^tag/)) {
            options.params.name = state.tagName
            dispatch(streamStoreOperations.getTagStream, options)
        } else if (state.streamName.match(/^profile_all/)) {
            options.params.id = state.applicationStore.profile.id
            dispatch(streamStoreOperations.getProfileAll, options)
        } else if (state.streamName.match(/^profile_pinned/)) {
            options.params.id = state.applicationStore.profile.id
            dispatch(streamStoreOperations.getProfilePinned, options)
        }
    },
    [streamStoreOperations.receivedNewContent]({commit}, newContentLengh) {
        commit(streamStoreOperations.receivedNewContent, newContentLengh)
    },
    [streamStoreOperations.newContentAck]({commit}) {
        commit(streamStoreOperations.newContentAck)
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
}

export {actions, mutations, streamStoreOperations, getters}
