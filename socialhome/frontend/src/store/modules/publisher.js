/* eslint-disable no-param-reassign */
const state = {}
const getters = {}
const mutations = {}

function actions(Axios) {
    return {
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

            return Axios
                .post(Urls["api:content-list"](), payload)
                .then(({data}) => Urls["content:view"]({pk: data.id}))
        },

        publishReply(_, {parent, showPreview = true, text, recipients}) {
            const payload = {
                parent,
                show_preview: showPreview,
                text,
                recipients,
            }

            return Axios
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

            return Axios
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

            return Axios
                .patch(Urls["api:content-detail"]({pk: contentId}), payload)
                .then(({data}) => Urls["content:view"]({pk: data.id}))
        },
    }
}

function getPublisherStore(Axios) {
    return {
        namespaced: true,
        state,
        getters,
        actions: actions(Axios),
        mutations,
    }
}

export default getPublisherStore
export {getPublisherStore}
