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
    follow({commit}, {uuid}) {
        return Vue.axios
            .post(Urls["api:profile-follow"]({uuid}))
            .then(() => commit("setFollow", {uuid, status: true}))
            .catch(() => {
                commit("application/setErrorMessage", gettext("An error happened while trying to follow."))
            })
    },
    getProfile({commit}, {uuid}) {
        return Vue.axios
            .get(Urls["api:profile-detail"]({uuid}))
            .then(result => commit("setProfile", result.data))
    },
    unFollow({commit}, {uuid}) {
        return Vue.axios
            .post(Urls["api:profile-unfollow"]({uuid}))
            .then(() => commit("setFollow", {uuid, status: false}))
            .catch(() => {
                commit("application/setErrorMessage", gettext("An error happened while trying to unfollow."))
            })
    },
}

const mutations = {
    setFollow(state, {uuid, status}) {
        Vue.set(state.all[uuid], "user_following", status)
    },
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
