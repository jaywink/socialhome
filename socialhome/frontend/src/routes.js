import VueRouter from "vue-router"
import _isString from "lodash/isString"

import Stream from "@/components/streams/Stream.vue"
import Publisher from "@/components/publisher/Publisher"
import ReplyPublisher from "@/components/publisher/ReplyPublisher"
import AppFollowing from "@/components/contacts/AppFollowing"
import AppFollowers from "@/components/contacts/AppFollowers"
import EditDispatcher from "@/components/publisher/EditDispatcher"

function $$(props = {}) {
    return route => ({
        ...(route.params), ...props,
    })
}

function publisherProps(route) {
    if (_isString(route.query.url) && _isString(route.query.title)) {
        return {
            shareUrl: route.query.url,
            shareTitle: route.query.title,
            shareNotes: route.query.notes !== undefined ? route.query.notes : "",
        }
    }
    return {}
}

const routes = [
    // Contacts page
    {
        path: "/p/~following/", component: AppFollowing,
    },
    {
        path: "/p/~followers/", component: AppFollowers,
    },

    // TODO: Matching "/" is a bit tricky since the stream can be customized.
    // TODO: In the future, Stream can be replaced by a generic RootStream.vue that just delegates to another component
    {
        path: "/", component: Stream,
    },
    {
        path: "/streams/followed", component: Stream,
    },
    {
        path: "/streams/limited", component: Stream,
    },
    {
        path: "/streams/local", component: Stream,
    },
    {
        path: "/streams/public", component: Stream,
    },
    {
        path: "/u/:user", component: Stream, props: $$(),
    },
    {
        path: "/u/:user/all", component: Stream, props: $$(),
    },
    {
        path: "/p/:uuid", component: Stream, props: $$(),
    },
    {
        path: "/p/:uuid/all", component: Stream, props: $$(),
    },
    {
        path: "/streams/tag/:tag", component: Stream, props: $$(),
    },
    {
        path: "/streams/tags/", component: Stream,
    },

    // Publisher
    {
        path: "/content/create",
        component: Publisher,
        props: publisherProps,
        alias: "/bookmarklet",
    },
    {
        path: "/content/:contentId/~reply/",
        component: ReplyPublisher,
        props: route => ({parentId: route.params.contentId}),
    },
    {
        path: "/content/:contentId/~edit/", component: EditDispatcher, props: $$(),
    },

    {
        path: "/content/:contentId", component: Stream, props: $$(),
    },
    {
        path: "/content/:contentId/:shorttext", component: Stream, props: $$(),
    },
]

const router = new VueRouter({
    routes, mode: "history",
})

export {routes, router}
export default router
