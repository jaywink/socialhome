import Vue from "vue"
import Vuex from "vuex"

import application from "@/store/modules/application"
import contacts from "@/store/modules/contacts"
import profile from "@/store/modules/profile"
import publisher from "@/store/modules/publisher"
import stream from "@/store/modules/stream"

Vue.use(Vuex)

const debug = process.env.NODE_ENV !== "production"

export default new Vuex.Store({
    modules: {
        application,
        contacts,
        profile,
        publisher,
        stream,
    },
    strict: debug,
})
