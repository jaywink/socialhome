import Vue from "vue"
import Vuex from "vuex"

import application from "@/store/modules/application"
import getContactsStore from "@/store/modules/contacts"
import user from "@/store/modules/user"
import profiles from "@/store/modules/profiles"
import publisher from "@/store/modules/publisher"
import stream, {profilesPlugin} from "@/store/modules/stream"

Vue.use(Vuex)

const debug = process.env.NODE_ENV !== "production"

export default new Vuex.Store({
    modules: {
        application,
        contacts: getContactsStore(Vue.axios),
        profiles,
        publisher,
        stream,
        user,
    },
    plugins: [profilesPlugin],
    strict: debug,
})
