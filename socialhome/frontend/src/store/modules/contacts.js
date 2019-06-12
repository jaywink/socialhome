/* eslint-disable no-param-reassign */
import Vue from "vue"
import Vapi from "vuex-rest-api"

import _isString from "lodash/isString"


const state = {
    followed: {
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

const options = {
    baseURL: "",
    axios: Vue.axios,
    state,
}

function onSuccess(stateTarget, data) {
    stateTarget.count = data.count
    stateTarget.next = _isString(data.next) ? new URL(data.next).searchParams.get("page") : null
    data.results.forEach(contact => stateTarget.contacts.push(contact))
}

function getContactFn(key) {
    return ({page = undefined, pageSize = undefined} = {}) => {
        const params = []
        if (page) params.push(`page=${page}`)
        if (pageSize) params.push(`page_size=${pageSize}`)

        const url = Urls[key]()

        return params.length === 0 ? url : `${url}?${params.join("&")}`
    }
}

const store = new Vapi(options)
    .get({
        action: "contactsFollowers",
        path: getContactFn("api:profile-followers"),
        property: "followers",
        onSuccess: (localState, {data}) => onSuccess(localState.followers, data),
    })
    .get({
        action: "contactsFollowed",
        path: getContactFn("api:profile-followed"),
        property: "followed",
        onSuccess: (localState, {data}) => onSuccess(localState.followed, data),
    })
    .getStore()

export default {namespaced: true, ...store}
/* eslint-enable no-param-reassign */
