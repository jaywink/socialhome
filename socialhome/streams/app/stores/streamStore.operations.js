const stateOperations = {
    receivedNewContent: "receivedNewContent",
    newContentAck: "newContentAck",
}

// This is the Vuex way
/* eslint-disable no-param-reassign */
const mutations = {
    [stateOperations.receivedNewContent](state, newContentLengh) {
        state.stream.hasNewContent = true
        state.stream.newContentLengh += newContentLengh
    },
    [stateOperations.newContentAck](state) {
        state.stream.hasNewContent = false
        state.stream.newContentLengh = 0
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
