import VueRouter from "vue-router"
import Stream from "frontend/components/streams/Stream.vue"


function $$(props = {}) {
    return route => Object.assign({}, route.params, props)
}

const routes = [
    // TODO: Matching '/' is a bit tricky since the stream can be customized.
    // TODO: In the future, Stream can be replaced by a generic RootStream.vue that just delegates to another component
    {path: "/", component: Stream},
    {path: "/streams/followed", component: Stream},
    {path: "/streams/limited", component: Stream},
    {path: "/streams/local", component: Stream},
    {path: "/streams/public", component: Stream},
    {path: "/u/:user", component: Stream, props: $$()},
    {path: "/u/:user/all", component: Stream, props: $$()},
    {path: "/p/:uuid", component: Stream, props: $$()},
    {path: "/p/:uuid/all", component: Stream, props: $$()},
    {path: "/streams/tag/:tag", component: Stream, props: $$()},
    {path: "/content/:contentId", component: Stream, props: $$()},
    {path: "/content/:contentId/:shorttext", component: Stream, props: $$()},
]

const router = new VueRouter({routes, mode: "history"})

export {routes, router}
export default router
