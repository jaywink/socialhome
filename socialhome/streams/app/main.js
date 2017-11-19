import Vue from "vue"
import BootstrapVue from "bootstrap-vue"
import infiniteScroll from "vue-infinite-scroll"
import VueMasonryPlugin from "vue-masonry"

import Axios from "axios"

import "streams/app/components/Stream.vue"


Vue.use(BootstrapVue)
Vue.use(infiniteScroll)
Vue.use(VueMasonryPlugin)

Vue.prototype.$http = Axios.create({
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFToken",
})

const main = new Vue({el: "#app"})

export default main
