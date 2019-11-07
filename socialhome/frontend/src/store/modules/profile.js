/* eslint-disable no-shadow */
import _get from "lodash/get"
import _without from "lodash/without"
import Vue from "vue"

const state = {..._get(window, ["context", "ownProfile"], {})}

const getters = {}

const actions = {
    followTag({commit}, name) {
        commit("followTag", name)
    },
    unfollowTag({commit}, name) {
        commit("unfollowTag", name)
    },
}

const mutations = {
    followTag(state, name) {
        if (!state.followed_tags.includes(name)) {
            state.followed_tags.push(name)
        }
    },
    unfollowTag(state, name) {
        if (state.followed_tags.includes(name)) {
            Vue.set(state, "followed_tags", _without(state.followed_tags, name))
        }
    },
}

export default {
    namespaced: true,
    state,
    getters,
    actions,
    mutations,
}
