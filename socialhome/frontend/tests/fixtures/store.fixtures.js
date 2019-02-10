import {getFakeContent, getProfile} from "frontend/tests/fixtures/jsonContext.fixtures"
import getStreamState from "../../store/modules/stream.state"
import {getters} from "../../store/modules/stream"

const getStore = () => {
    const store = {state: {}}
    store.state.stream = getStreamState()
    store.state.profile = {}
    store.state.application = {}
    store.content = getFakeContent()
    store.reply = getFakeContent({parent: store.content.id, content_type: "reply"})
    store.share = getFakeContent({share_of: store.content.id, content_type: "share"})
    store.shareReply = getFakeContent({share_of: store.share.id, content_type: "reply"})

    store.content.replyIds = [store.reply.id]
    store.share.replyIds = [store.shareReply.id]
    store.content.shareIds = [store.share.id]
    store.state.stream.contentIds.push(store.content.id)

    store.profile = getProfile()

    store.state.stream.contents[store.content.id] = store.content
    store.state.stream.replies[store.reply.id] = store.reply
    store.state.stream.shares[store.share.id] = store.share
    store.state.stream.replies[store.shareReply.id] = store.shareReply
    store.state.stream.pending = {
        contents: false,
        replies: false,
        shares: false,
    }

    store.state.stream.stream.id = ""
    store.state.stream.stream.isProfile = false
    store.state.stream.stream.name = "public"
    store.state.stream.stream.single = false

    store.state.application.currentBrowsingProfileId = store.profile.id
    store.state.application.isUserAuthenticated = true
    store.state.application.profile = store.profile

    store.getters = {
        "stream/replies": getters.replies,
        "stream/shares": getters.shares,
    }
    store.dispatch = () => {}

    return store
}

export {getStore}
