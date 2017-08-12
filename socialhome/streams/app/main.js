import Vue from "vue"
import VueResource from "vue-resource"
import BootstrapVue from "bootstrap-vue/dist/bootstrap-vue.esm"
import "streams/app/stores/streamStore"
import "streams/app/components/Stream.vue"

Vue.use(VueResource)
Vue.use(BootstrapVue)

export default new Vue({
    el: "#app",
    http: {root: "/"}
})
