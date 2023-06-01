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
    getProfileSelection: state => selection => {
        const profiles = []
        selection.forEach(profile => {
            profiles.push(state.all[profile.uuid])
        })
        return profiles
    },
    getByUuid: state => uuid => state.all[uuid],
}

const actions = {
    follow({commit}, {uuid}) {
        return Vue.axios
            .post(Urls["api:profile-follow"]({uuid}))
            .then(() => commit("setFollow", {
                uuid, status: true,
            }))
            .catch(() => {
                Vue.snotify.error(gettext("An error happened while trying to follow."))
            })
    },
    getProfile({commit}, {uuid}) {
        return Vue.axios
            .get(Urls["api:profile-detail"]({uuid}))
            .then(result => commit("setProfile", result.data))
            .catch(() => {
                Vue.snotify.error(gettext("An error happened while fetching a profile."))
            })
    },
    // eslint-disable-next-line no-unused-vars
    requestProfileUpdate({commit}, {uuid}) {
        return Vue.axios
            .get(Urls["api:profile-schedule-update"]({uuid}))
            .then()
            .catch(() => {
                Vue.snotify.error(gettext("An error happened while requesting a profile update."))
            })
    },
    unFollow({commit}, {uuid}) {
        return Vue.axios
            .post(Urls["api:profile-unfollow"]({uuid}))
            .then(() => commit("setFollow", {
                uuid, status: false,
            }))
            .catch(() => {
                Vue.snotify.error(gettext("An error happened while trying to unfollow."))
            })
    },
}

const mutations = {
    setFollow(state, {uuid, status}) {
        Vue.set(state.all[uuid], "user_following", status)
    },
    setProfile(state, profile) {
        if (state.index.indexOf(profile.uuid) === -1) {
            Vue.set(state.all, profile.uuid, profile)
            state.index.push(profile.uuid)
        } else {
            Vue.set(state.all, profile.uuid, Object.assign(state.all[profile.uuid], profile))
        }
    },
    setProfilesFromContentList(state, contentList) {
        contentList.forEach(content => {
            if (state.index.indexOf(content.author.uuid) === -1) {
                Vue.set(state.all, content.author.uuid, content.author)
                state.index.push(content.author.uuid)
            }
            if (content.through_author) {
                if (state.index.indexOf(content.through_author.uuid) === -1) {
                    Vue.set(state.all, content.through_author.uuid, content.through_author)
                    state.index.push(content.through_author.uuid)
                }
            }
        })
    },
    setProfilesFromContactList(state, contactList) {
        contactList.forEach(contact => {
            if (state.index.indexOf(contact.uuid) === -1) {
                Vue.set(state.all, contact.uuid, contact)
                state.index.push(contact.uuid)
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
