/* eslint-disable no-param-reassign */
import Vue from "vue"


const state = {}
const getters = {}
const mutations = {}

const actions = {
    // eslint-disable-next-line object-curly-newline
    publishPost(_, {
        federate = true,
        includeFollowing = false,
        pinned = false,
        recipients = "",
        showPreview = true,
        text,
        visibility,
    }) {
        const payload = {
            federate,
            include_following: includeFollowing,
            order: 0,
            pinned,
            recipients,
            show_preview: showPreview,
            service_label: "",
            text,
            visibility,
        }

        return Vue.axios
            .post(Urls["api:content-list"](), payload)
            .then(({data}) => Urls["content:view"]({pk: data.id}))
    },

    publishReply(_, {parent, showPreview = true, text}) {
        const payload = {
            parent,
            show_preview: showPreview,
            text,
        }

        return Vue.axios
            .post(Urls["api:content-list"](), payload)
            .then(({data}) => Urls["content:view"]({pk: data.id}))
    },

    editPost(_, {
        contentId,
        federate = true,
        includeFollowing = false,
        pinned = false,
        recipients = "",
        showPreview = true,
        text,
        visibility,
    }) {
        const payload = {
            federate,
            include_following: includeFollowing,
            order: 0,
            pinned,
            recipients,
            show_preview: showPreview,
            service_label: "",
            text,
            visibility,
        }

        return Vue.axios
            .patch(Urls["api:content-detail"]({pk: contentId}), payload)
            .then(({data}) => Urls["content:view"]({pk: data.id}))
    },

    // eslint-disable-next-line object-curly-newline
    editReply(_, {contentId, parent, showPreview = true, text}) {
        const payload = {
            parent,
            show_preview: showPreview,
            text,
        }

        return Vue.axios
            .patch(Urls["api:content-detail"]({pk: contentId}), payload)
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
