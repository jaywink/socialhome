/* eslint-disable no-param-reassign */
import Vue from "vue"
import _concat from "lodash/concat"
import _difference from "lodash/difference"

const streamMutations = {
    disableLoadMore(state, contentId) {
        Vue.set(state.contents[contentId], "hasLoadMore", false)
    },
    receivedNewContent(state, contentId) {
        state.unfetchedContentIds.push(contentId)
    },
    setLayoutDoneAfterTwitterOEmbeds(state, status) {
        state.layoutDoneAfterTwitterOEmbeds = status
    },
    newContentAck(state) {
    /*
         * First, get all IDs present in unfetchedContentIds and absent in contentIds
         * This is neccessary since content ids that could not be fetched due to
         * network errors are not removed from `state.unfetchedContentIds`. In this
         * case, the next time unfetched content is fetched, these ids would be added
         * twice and appear twice in the stream.
         */
        const diff = _difference(state.unfetchedContentIds, state.contentIds)
        Vue.set(state, "contentIds", _concat(diff, state.contentIds))
        state.unfetchedContentIds.length = 0
    },
}

const streamActions = {
    disableLoadMore({commit}, contentId) {
        commit("disableLoadMore", contentId)
    },
    receivedNewContent({commit}, newContentLengh) {
        commit("receivedNewContent", newContentLengh)
    },
    setLayoutDoneAfterTwitterOEmbeds({commit}, status) {
        commit("setLayoutDoneAfterTwitterOEmbeds", status)
    },
    newContentAck({commit, dispatch, state}) {
        const promises = []
        const unfetchedContentIds = _concat([], state.unfetchedContentIds)

        commit("newContentAck")

        unfetchedContentIds.forEach(pk => {
            // Force the promise to resolve in all cases
            const reAddAndResolve = () => {
                state.unfetchedContentIds.push(pk)
                return Promise.resolve()
            }
            const promise = dispatch("getNewContent", {params: {pk}})
                .then(Promise.resolve(), reAddAndResolve)
            promises.push(promise)
        })
        return Promise.all(promises)
    },
}

const streamGetters = {
    contentList(state) {
        const contents = []
        state.contentIds.forEach(id => {
            if (state.contents[id] !== undefined) {
                contents.push(state.contents[id])
            }
        })
        return contents
    },
    replies: state => content => {
        const replies = []
        if (content.content_type === "content") {
            state.contents[content.id].replyIds.forEach(id => {
                replies.push(state.replies[id])
            })
        } else if (content.content_type === "share") {
            state.shares[content.id].replyIds.forEach(id => {
                replies.push(state.replies[id])
            })
        }
        return replies
    },
    shares: state => contentId => {
        const shares = []
        state.contents[contentId].shareIds.forEach(id => {
            shares.push(state.shares[id])
        })
        return shares
    },
    hasNewContent(state) {
        return state.unfetchedContentIds.length > 0 && !state.pending.contents
    },
}

export {streamActions, streamMutations, streamGetters}
