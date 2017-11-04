import Vue from "vue"

import {getFakePost} from "streams/app/tests/fixtures/jsonContext.fixtures"
import {newStreamStore} from "streams/app/stores/streamStore"
import applicationStore from "streams/app/stores/applicationStore"


const getStore = function() {
    let store = newStreamStore({ modules: { applicationStore } })
    const fakePost = getFakePost()
    store.state.contentIds.push(fakePost.id)
    Vue.set(store.state.contents, fakePost.id, fakePost)
    Vue.set(store.state.replyIds, fakePost.id, [])
    Vue.set(store.state.shareIds, fakePost.id, [])
    store.state.applicationStore.isUserAuthenticated = true
    store.state.applicationStore.profile = {id: fakePost.author.id}
    return store
}

export {getStore}
