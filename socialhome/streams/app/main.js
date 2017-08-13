import Vue from "vue"
import VueMasonry from "vue-masonry"
import BootstrapVue from "bootstrap-vue"

import Axios from "axios"

import "streams/app/components/Stream.vue"


Vue.use(VueMasonry)
Vue.use(BootstrapVue)

Vue.prototype.$http = Axios.create({
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFToken",
})

export default new Vue({el: "#app"})
