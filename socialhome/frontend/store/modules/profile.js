import _get from "lodash/get"

const state = {
    authenticated: _get(window, ["context", "isUserAuthenticated"], false),
    profile: _get(window, ["context", "currentBrowsingProfile"], {}),
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
