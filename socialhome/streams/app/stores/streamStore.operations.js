const streamStoreOperations = {
    getFollowedStream: "getFollowedStream",
    getNewContent: "getNewContent",
    getProfileAll: "getProfileAll",
    getProfilePinned: "getProfilePinned",
    getPublicStream: "getPublicStream",
    getTagStream: "getTagStream",
    newContentAck: "newContentAck",
    receivedNewContent: "receivedNewContent",
}

// This is the Vuex way
/* eslint-disable no-param-reassign */
const mutations = {
    [streamStoreOperations.receivedNewContent](state, contentId) {
        state.unfetchedContentIds.push(contentId)
    },
}
/* eslint-enable no-param-reassign */

const actions = {
    [streamStoreOperations.receivedNewContent]({commit}, newContentLengh) {
        commit(streamStoreOperations.receivedNewContent, newContentLengh)
    },
    [streamStoreOperations.newContentAck]({dispatch, state}) {
        state.unfetchedContentIds.forEach(pk => {
            dispatch(streamStoreOperations.getNewContent, {params: {pk}})
        })
    },
}

const getters = {
    hasNewContent(state) {
        return state.unfetchedContentIds.length > 0
    },
}

export {actions, mutations, streamStoreOperations, getters}
