/* eslint-disable no-shadow */
import _get from "lodash/get"

export const applicationPlugin = store => {
    // called when the store is initialized
    store.subscribe(({type, payload}) => {
        // eslint-disable-next-line no-console
        console.log(type, payload)
        if (/^stream\/GET[A-Z_]*SUCCEEDED$/.test(type)) {
            store.commit("profiles/setProfilesFromContentList", payload.payload.data, {root: true})
        }
    })
}

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
