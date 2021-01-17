import Axios from "axios"
import VueAxios from "vue-axios"
import BootstrapVue from "bootstrap-vue/dist/bootstrap-vue.esm"
import InfiniteLoading from "vue-infinite-loading"
import VueInfiniteScroll from "vue-infinite-scroll"
import {VueMasonryPlugin} from "vue-masonry"
import VueRouter from "vue-router"
import VueSnotify from "vue-snotify"
import VueScrollTo from "vue-scrollto"

import filters from "@/filters"
import LoadingElement from "@/components/common/LoadingElement"
import NoMoreDataEement from "@/components/common/NoMoreDataEement"

const VueDeviceSize = Object.freeze({
    // eslint-disable-next-line object-curly-newline
    install(Vue, {smSize = 576, mdSize = 768, lgSize = 992, xlSize = 1200} = {}) {
        if (VueDeviceSize.install.installed === true) {
            return
        }

        /* eslint-disable no-param-reassign */
        Vue.prototype.$deviceSize = Vue.observable({
            isMaxSm: false,
            isMaxMd: false,
            isMaxLg: false,
            isMaxXl: false,
            isMinSm: false,
            isMinMd: false,
            isMinLg: false,
            isMinXl: false,
        })
        // eslint-disable-next-line no-param-reassign
        Vue.deviceSize = Vue.prototype.$deviceSize
        VueDeviceSize.install.installed = true

        function onResize() {
            Vue.prototype.$deviceSize.isMaxSm = window.innerWidth < smSize
            Vue.prototype.$deviceSize.isMaxMd = window.innerWidth < mdSize
            Vue.prototype.$deviceSize.isMaxLg = window.innerWidth < lgSize
            Vue.prototype.$deviceSize.isMaxXl = window.innerWidth < xlSize
            Vue.prototype.$deviceSize.isMinSm = window.innerWidth >= smSize
            Vue.prototype.$deviceSize.isMinMd = window.innerWidth >= mdSize
            Vue.prototype.$deviceSize.isMinLg = window.innerWidth >= lgSize
            Vue.prototype.$deviceSize.isMinXl = window.innerWidth >= xlSize
        }

        function onLoadEnd() {
            onResize()
            window.addEventListener("resize", onResize)
            window.addEventListener("beforeunload",
                () => window.removeEventListener("resize", onResize))
            window.removeEventListener("load", onLoadEnd)
        }

        window.addEventListener("load", onLoadEnd)
        /* eslint-enable no-param-reassign */
    },
})

export default function (Vue) {
    Vue.use(BootstrapVue)
    Vue.use(VueInfiniteScroll)

    Vue.use(VueMasonryPlugin)
    Vue.use(VueRouter)
    Vue.use(VueSnotify)
    Vue.use(VueScrollTo)
    Vue.snotify = Vue.prototype.$snotify // eslint-disable-line no-param-reassign

    const axios = Axios.create({
        xsrfCookieName: "csrftoken",
        xsrfHeaderName: "X-CSRFToken",
    })

    Vue.use(VueAxios, axios)
    Vue.use(VueDeviceSize)
    Vue.use(InfiniteLoading, {
        slots: {
            spinner: LoadingElement,
            noMore: NoMoreDataEement,
        },
    })

    // Globally add filters
    Object.entries(filters).forEach(([key, value]) => Vue.filter(`${key}`, value))
}
