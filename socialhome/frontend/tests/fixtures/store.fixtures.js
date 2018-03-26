import Axios from "axios"
import Vue from "vue"

import {getFakeContent, getProfile} from "frontend/tests/fixtures/jsonContext.fixtures"
import applicationStore from "frontend/stores/applicationStore"
import {newStreamStore} from "frontend/stores/streamStore"


const getStore = () => {
    const store = newStreamStore({
        modules: {applicationStore},
        baseURL: "",
        axios: Axios.create({
            xsrfCookieName: "csrftoken",
            xsrfHeaderName: "X-CSRFToken",
        }),
    })
    store.content = getFakeContent()
    store.reply = getFakeContent({parent: store.content.id, content_type: "reply"})
    store.share = getFakeContent({share_of: store.content.id, content_type: "share"})
    store.shareReply = getFakeContent({share_of: store.share.id, content_type: "reply"})

    store.content.replyIds = [store.reply.id]
    store.share.replyIds = [store.shareReply.id]
    store.content.shareIds = [store.share.id]
    store.state.contentIds.push(store.content.id)

    store.profile = getProfile()

    Vue.set(store.state.contents, store.content.id, store.content)
    Vue.set(store.state.replies, store.reply.id, store.reply)
    Vue.set(store.state.shares, store.share.id, store.share)
    Vue.set(store.state.replies, store.shareReply.id, store.shareReply)

    Vue.set(store.state.stream, "id", "")
    Vue.set(store.state.stream, "isProfile", false)
    Vue.set(store.state.stream, "name", "public")
    Vue.set(store.state.stream, "single", false)

    store.state.applicationStore.currentBrowsingProfileId = store.profile.id
    store.state.applicationStore.isUserAuthenticated = true
    store.state.applicationStore.profile = store.profile
    return store
}

export {getStore}
