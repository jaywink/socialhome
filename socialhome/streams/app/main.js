import Vue from "vue"
import VueResource from "vue-resource"
import "./stores/streamStore"
import "./components/Stream.vue"
import Modal from "../../shared/ModalContainer"

Vue.use(VueResource)

const modalView = new Modal({el: "#vue-modal"})

export default new Vue({
    el: "#app",
    http: {root: "/"}
})

export {modalView}
