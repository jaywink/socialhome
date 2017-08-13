import Vue from "vue"
import Vuex from "vuex"
import VueResource from "vue-resource"

// Vue setup
Vue.use(Vuex)
Vue.use(VueResource)

export default new Vuex.Store({
    state: {
        translations: {
            stampedContent: {
                h2: window.context.translations.stampedContent.h2,
                p: window.context.translations.stampedContent.p,
            },
        },
        contentList: window.context.contentList,
        streamName: window.context.streamName,
        isUserAuthentificated: window.context.isUserAuthentificated,
        showAuthorBar: window.context.showAuthorBar,
    },
})
