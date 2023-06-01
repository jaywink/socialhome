/* eslint-disable no-param-reassign */
import Vapi from "vuex-rest-api"

import _isString from "lodash/isString"
import profiles from "@/store/modules/profiles"

function getState() {
    return {
        following: {
            count: 1,
            next: null,
            contacts: [],
        },
        followers: {
            count: 1,
            next: null,
            contacts: [],
        },
    }
}

function onSuccess(stateTarget, data) {
    stateTarget.count = data.count
    stateTarget.next = _isString(data.next) ? new URL(data.next).searchParams.get("page") : null
    data.results.forEach(contact => stateTarget.contacts.push(contact))
    profiles.mutations.setProfilesFromContactList(profiles.state, data.results)
}

function getContactFn(key) {
    return ({page = undefined, pageSize = undefined} = {}) => {
        const params = []
        if (page) {
            params.push(`page=${page}`)
        }
        if (pageSize) {
            params.push(`page_size=${pageSize}`)
        }

        const url = Urls[key]()

        return params.length === 0 ? url : `${url}?${params.join("&")}`
    }
}

function getContactsStore(axios) {
    const options = {
        baseURL: "",
        axios,
        state: getState(),
    }

    const store = new Vapi(options)
        .get({
            action: "contactsFollowers",
            path: getContactFn("api:profile-followers"),
            property: "followers",
            onSuccess: (localState, {data}) => onSuccess(localState.followers, data),
        })
        .get({
            action: "contactsFollowing",
            path: getContactFn("api:profile-following"),
            property: "following",
            onSuccess: (localState, {data}) => onSuccess(localState.following, data),
        })
        .getStore()

    return {
        namespaced: true,
        state: store.state,
        getters: store.getters,
        actions: store.actions,
        mutations: store.mutations,
    }
}

export {getContactsStore}
export default getContactsStore
/* eslint-enable no-param-reassign */
