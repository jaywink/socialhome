import Vue from "vue"
import Vuex from "vuex"

// Vue setup
Vue.use(Vuex)

function getContext() {
    try {
        return {
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
                currentBrowsingProfileId: (window.context.currentBrowsingProfileId
                    ? `${window.context.currentBrowsingProfileId}`
                    : void(0)),
            },
        }
    }
    catch (_) {
        return {}
    }
}

export default new Vuex.Store(getContext())
