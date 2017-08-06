import Vue from "vue"
import VueResource from "vue-resource"
import "./stores/streamStore"
import "./components/Stream.vue"

Vue.use(VueResource)

export default new Vue({
    el: "#app",
    http: {root: "/"}
})
