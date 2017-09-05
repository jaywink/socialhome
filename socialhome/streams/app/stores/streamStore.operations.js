import Vue from "vue"

const streamStoreOperations = {
    receivedNewContent: "receivedNewContent",
    newContentAck: "newContentAck",
}

// This is the Vuex way
/* eslint-disable no-param-reassign */
const mutations = {
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
}

export {actions, mutations, streamStoreOperations, getters}
