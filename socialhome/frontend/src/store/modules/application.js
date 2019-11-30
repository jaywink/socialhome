/* eslint-disable no-shadow */
import _get from "lodash/get"

const state = {
    isUserAuthenticated: _get(window, ["context", "isUserAuthenticated"], false),
    currentBrowsingProfileId: _get(window, ["context", "currentBrowsingProfileId"]),
    profile: _get(window, ["context", "profile"]),
    errorMessage: null,
}

const getters = {}

const actions = {}

const mutations = {
    setErrorMessage(state, message) {
        // eslint-disable-next-line no-param-reassign
        state.errorMessage = message
    },
}

export default {
    namespaced: true,
    state,
    getters,
    actions,
    mutations,
}
