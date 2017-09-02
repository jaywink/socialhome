import Vue from "vue"
import Vuex from "vuex"
import _isNumber from "lodash/isNumber"
import _get from "lodash/get"


Vue.use(Vuex)

function newApplicationStore() {
    return new Vuex.Store({
        state: {
            isUserAuthenticated: _get(window, ["context", "isUserAuthenticated"], false),
            currentBrowsingProfileId: (_isNumber(_get(window, ["context", "currentBrowsingProfileId"], undefined))
                ? `${window.context.currentBrowsingProfileId}` : undefined),
        },
    })
}

const applicationStore = newApplicationStore()
export default applicationStore
export {applicationStore, newApplicationStore}
