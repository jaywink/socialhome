import Vue from "vue"
import Vuex from "vuex"
import isNil from "lodash/isNil"

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
                currentBrowsingProfileId: (isNil(window.context.currentBrowsingProfileId)
                    ? `${window.context.currentBrowsingProfileId}` : undefined),
            },
        }
    } catch (_) {
        return {}
    }
}

export default new Vuex.Store(getContext())
