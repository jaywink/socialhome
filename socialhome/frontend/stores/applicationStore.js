import Vue from "vue"
import Vuex from "vuex"
import _get from "lodash/get"


Vue.use(Vuex)

function newApplicationStore() {
    return new Vuex.Store({
        state: {
            isUserAuthenticated: _get(window, ["context", "isUserAuthenticated"], false),
            currentBrowsingProfileId: _get(window, ["context", "currentBrowsingProfileId"]),
            // TODO: To be removed
            profile: _get(window, ["context", "profile"]),
        },
    })
}

const applicationStore = newApplicationStore()
export default applicationStore
export {applicationStore, newApplicationStore}
