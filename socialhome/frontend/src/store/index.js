import Vuex from "vuex"

import application from "@/store/modules/application"
import getContactsStore from "@/store/modules/contacts"
import user from "@/store/modules/user"
import profiles from "@/store/modules/profiles"
import {getPublisherStore} from "@/store/modules/publisher"
import {profilesPlugin, getStreamStore} from "@/store/modules/stream"

const debug = process.env.NODE_ENV !== "production"

function getStore(Vue) {
    Vue.use(Vuex)

    return new Vuex.Store({
        modules: {
            application,
            contacts: getContactsStore(Vue.axios),
            profiles,
            publisher: getPublisherStore(Vue.axios),
            stream: getStreamStore(),
            user,
        },
        plugins: [profilesPlugin],
        strict: debug,
    })
}

export default getStore
export {getStore}
