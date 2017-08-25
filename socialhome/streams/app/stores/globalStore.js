import Vue from "vue"
import Vuex from "vuex"
import _isNumber from "lodash/isNumber"
import _get from "lodash/get"


Vue.use(Vuex)

function newinstance() {
    return new Vuex.Store({
        state: {
            translations: {
                stampedContent: {
                    h2: _get(window, ["context", "translations", "stampedContent", "h2"], ""),
                    p: _get(window, ["context", "translations", "stampedContent", "p"], ""),
                },
            },
            isUserAuthenticated: _get(window, ["context", "isUserAuthenticated"], false),
            currentBrowsingProfileId: (_isNumber(_get(window, ["context", "currentBrowsingProfileId"], undefined))
                ? `${window.context.currentBrowsingProfileId}` : undefined),
        },
    })
}

const store = newinstance()
export default store
export {store, newinstance}
