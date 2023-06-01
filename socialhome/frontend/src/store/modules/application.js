/* eslint-disable no-shadow */
import _get from "lodash/get"

const state = {
    isUserAuthenticated: _get(window, ["context", "isUserAuthenticated"], false),
    currentBrowsingProfileId: _get(window, ["context", "currentBrowsingProfileId"]),
    profile: _get(window, ["context", "profile"]),
}

const getters = {}

const actions = {}

const mutations = {}

export default {
    namespaced: true,
    state,
    getters,
    actions,
    mutations,
}
