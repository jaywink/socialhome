import Vue from "vue"

import {getFakeContent} from "streams/app/tests/fixtures/jsonContext.fixtures"
import {newStreamStore} from "streams/app/stores/streamStore"
import applicationStore from "streams/app/stores/applicationStore"


const getStore = function() {
    let store = newStreamStore({ modules: { applicationStore } })
    store.content = getFakeContent()
    store.reply = getFakeContent({parent: store.content.id, content_type: "reply"})
    store.share = getFakeContent({share_of: store.content.id, content_type: "share"})
    store.shareReply = getFakeContent({share_of: store.share.id, content_type: "reply"})
    store.state.contentIds.push(store.content.id)
    Vue.set(store.state.contents, store.content.id, store.content)
    Vue.set(store.state.contents, store.reply.id, store.reply)
    Vue.set(store.state.contents, store.share.id, store.share)
    Vue.set(store.state.contents, store.shareReply.id, store.shareReply)
    Vue.set(store.state.replyIds, store.content.id, [store.reply.id])
    Vue.set(store.state.replyIds, store.share.id, [store.shareReply.id])
    Vue.set(store.state.shareIds, store.content.id, [store.share.id])
    store.state.applicationStore.isUserAuthenticated = true
    store.state.applicationStore.profile = {id: store.content.author.id}
    return store
}

export {getStore}
