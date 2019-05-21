/* eslint-disable no-param-reassign */
import Vue from "vue"

const state = {}
const getters = {}
const mutations = {}

const actions = {
    publishPost(_, {pinned, text, visibility, parent = null}) {
        const payload = {
            order: 0,
            parent,
            pinned,
            service_label: "",
            text,
            visibility,
        }

        return Vue.prototype.$http
            .post(Urls["api:content-list"](), payload)
            .then(({data}) => Urls["content:view"]({pk: data.id}))
    },
}

export default {
    namespaced: true,
    state,
    getters,
    actions,
    mutations,
}
