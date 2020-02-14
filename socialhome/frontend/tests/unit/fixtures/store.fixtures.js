import getStreamState from "@/store/modules/stream.state"
import {getters} from "@/store/modules/stream"
import {getFakeContent, getProfile} from "%fixtures/jsonContext.fixtures"

const getStore = () => {
    const store = {state: {}}
    store.state.stream = getStreamState()
    store.state.profile = {}
    store.state.application = {}
    store.content = getFakeContent()
    store.reply = getFakeContent({
        parent: store.content.id, content_type: "reply",
    })
    store.share = getFakeContent({
        share_of: store.content.id, content_type: "share",
    })
    store.shareReply = getFakeContent({
        share_of: store.share.id, content_type: "reply",
    })

    store.content.replyIds = [store.reply.id]
    store.share.replyIds = [store.shareReply.id]
    store.content.shareIds = [store.share.id]
    store.state.stream.currentContentIds.push(store.content.id)
    store.state.stream.allContentIds.push(store.content.id)
    store.state.stream.allContentIds.push(store.reply.id)
    store.state.stream.allContentIds.push(store.share.id)
    store.state.stream.allContentIds.push(store.shareReply.id)

    store.profile = getProfile()

    store.state.stream.contents[store.content.id] = store.content
    store.state.stream.contents[store.reply.id] = store.reply
    store.state.stream.contents[store.share.id] = store.share
    store.state.stream.contents[store.shareReply.id] = store.shareReply
    store.state.stream.pending = {
        contents: false,
        replies: false,
        shares: false,
    }

    store.state.stream.stream.id = ""
    store.state.stream.stream.name = "public"
    store.state.stream.stream.single = false

    store.state.application.currentBrowsingProfileId = store.profile.id
    store.state.application.isUserAuthenticated = true
    store.state.application.profile = store.profile

    store.state.profiles = {
        all: {},
        index: [
            store.profile.uuid,
            store.content.author.uuid,
            store.reply.author.uuid,
            store.share.author.uuid,
            store.shareReply.author.uuid,
        ],
    }
    store.state.profiles.all[store.profile.uuid] = store.profile
    store.state.profiles.all[store.content.author.uuid] = store.content.author
    store.state.profiles.all[store.reply.author.uuid] = store.reply.author
    store.state.profiles.all[store.share.author.uuid] = store.share.author
    store.state.profiles.all[store.shareReply.author.uuid] = store.shareReply.author

    store.getters = {
        "stream/replies": getters.replies,
        "stream/shares": getters.shares,
    }
    store.dispatch = () => {}

    return store
}

export {getStore}
export default getStore
