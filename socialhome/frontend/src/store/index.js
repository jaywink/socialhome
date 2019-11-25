import Vue from "vue"
import Vuex from "vuex"

import application from "@/store/modules/application"
import getContactsStore from "@/store/modules/contacts"
import profile from "@/store/modules/profile"
import profiles from "@/store/modules/profiles"
import publisher from "@/store/modules/publisher"
import stream, {profilesPlugin} from "@/store/modules/stream"

Vue.use(Vuex)

const debug = process.env.NODE_ENV !== "production"

export default new Vuex.Store({
    modules: {
        application,
        contacts: getContactsStore(Vue.axios),
        profile,
        profiles,
        publisher,
        stream,
    },
    plugins: [profilesPlugin],
    strict: debug,
})
