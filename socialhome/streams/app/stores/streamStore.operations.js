const stateOperations = {
    receivedNewContent: "receivedNewContent",
    newContentAck: "newContentAck",
}

// This is the Vuex way
/* eslint-disable no-param-reassign */
const mutations = {
    [stateOperations.receivedNewContent](state, contentId) {
        state.hasNewContent = true
        state.newContentLengh += 1
        state.contentList[contentId] = undefined
    },
    [stateOperations.newContentAck](state) {
        state.hasNewContent = false
        state.newContentLengh = 0
    },
}
/* eslint-enable no-param-reassign */

const actions = {
    [stateOperations.receivedNewContent]({commit}, newContentLengh) {
        commit(stateOperations.receivedNewContent, newContentLengh)
    },
    [stateOperations.newContentAck]({commit}) {
        commit(stateOperations.newContentAck)
    },
}

export {actions, mutations, stateOperations}
