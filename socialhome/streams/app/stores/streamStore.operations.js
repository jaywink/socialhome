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
    newContentAck: "newContentAck",
    receivedNewContent: "receivedNewContent",
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
