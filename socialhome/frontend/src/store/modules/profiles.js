/* eslint-disable no-shadow */
import Vue from "vue"

const state = {
    all: {},
    index: [],
}

const getters = {
    allProfiles: state => {
        const profiles = []
        state.index.forEach(uuid => {
            profiles.push(state.all[uuid])
        })
        return profiles
    },
    getByUuid: state => uuid => state.all[uuid],
}

const actions = {
    getProfile({commit}, {uuid}) {
        return Vue.axios
            .get(Urls["api:profile-detail"]({uuid}))
            .then(result => commit("setProfile", result.data))
    },
}

const mutations = {
    setProfile(state, profile) {
        Vue.set(state.all, profile.uuid, profile)
        if (state.index.indexOf(profile.uuid) === -1) {
            state.index.push(profile.uuid)
        }
    },
    setProfilesFromContentList(state, contentList) {
        contentList.forEach(content => {
            if (state.index.indexOf(content.author.uuid) === -1) {
                Vue.set(state.all, content.author.uuid, content.author)
                state.index.push(content.author.uuid)
            }
        })
    },
}

export default {
    namespaced: true,
    state,
    getters,
    actions,
    mutations,
}
