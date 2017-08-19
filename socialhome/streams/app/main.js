import Vue from "vue"
import {VueMasonryPlugin} from "vue-masonry"
import BootstrapVue from "bootstrap-vue"

import Axios from "axios"

import "./components/Stream.vue"


Vue.use(VueMasonryPlugin)
Vue.use(BootstrapVue)

Vue.prototype.$http = Axios.create({
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFToken",
})

export default new Vue({el: "#app"})
