const streamStoreOerations = {
    receivedNewContent: "receivedNewContent",
    newContentAck: "newContentAck",
}

// This is the Vuex way
/* eslint-disable no-param-reassign */
const mutations = {
    [streamStoreOerations.receivedNewContent](state, contentId) {
        state.hasNewContent = true
        state.newContentLengh += 1
        state.contentList[contentId] = undefined
    },
    [streamStoreOerations.newContentAck](state) {
        state.hasNewContent = false
        state.newContentLengh = 0
    },
}
/* eslint-enable no-param-reassign */

const actions = {
    [streamStoreOerations.receivedNewContent]({commit}, newContentLengh) {
        commit(streamStoreOerations.receivedNewContent, newContentLengh)
    },
    [streamStoreOerations.newContentAck]({commit}) {
        commit(streamStoreOerations.newContentAck)
    },
}

export {actions, mutations, streamStoreOerations}
