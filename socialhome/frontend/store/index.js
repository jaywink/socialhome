import Vue from 'vue'
import Vuex from 'vuex'

import application from "./modules/application"
import profile from "./modules/profile"
import stream from "./modules/stream"
import publisher from "./modules/publisher"

Vue.use(Vuex)

const debug = process.env.NODE_ENV !== 'production'

export default new Vuex.Store({
    modules: {
        application,
        profile,
        stream,
        publisher
    },
    strict: debug,
})
