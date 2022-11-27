/* eslint-disable no-param-reassign */
import Vue from "vue"
import _concat from "lodash/concat"
import _difference from "lodash/difference"
import _upperFirst from "lodash/upperFirst"

const streamMutations = {
    disableLoadMore(state, contentId) {
        Vue.set(state.contents[contentId], "hasLoadMore", false)
    },
    receivedNewContent(state, payload) {
        const {contentId, parentId} = payload
        if (parentId === null) {
            if (state.unfetchedContentIds.indexOf(contentId) === -1) {
                state.unfetchedContentIds.unshift(contentId)
            }
        } else if (state.allContentIds.indexOf(contentId) === -1 && state.contents[parentId] !== undefined) {
            state.contents[parentId].reply_count += 1
        }
    },
    setLayoutDoneAfterTwitterOEmbeds(state, status) {
        state.layoutDoneAfterTwitterOEmbeds = status
    },
    newContentAck(state) {
    /*
         * First, get all IDs present in unfetchedContentIds and absent in currentContentIds
         * This is neccessary since content ids that could not be fetched due to
         * network errors are not removed from `state.unfetchedContentIds`. In this
         * case, the next time unfetched content is fetched, these ids would be added
         * twice and appear twice in the stream.
         */
        const diff = _difference(state.unfetchedContentIds, state.currentContentIds)
        Vue.set(state, "currentContentIds", _concat(diff, state.currentContentIds))
        state.unfetchedContentIds.length = 0
    },
}

const streamActions = {
    disableLoadMore({commit}, contentId) {
        commit("disableLoadMore", contentId)
    },
    receivedNewContent({commit}, payload) {
        commit("receivedNewContent", payload)
    },
    setLayoutDoneAfterTwitterOEmbeds({commit}, status) {
        commit("setLayoutDoneAfterTwitterOEmbeds", status)
    },
    newContentAck({commit, dispatch, state}) {
        const unfetchedContentIds = _concat([], state.unfetchedContentIds)

        commit("newContentAck")
        const dispatchName = `get${_upperFirst(state.stream.name)}Stream`
        dispatch(dispatchName, {params: {acceptIds: unfetchedContentIds}})
    },
}

const streamGetters = {
    contentById: state => contentId => state.contents[contentId],
    currentContentList(state) {
        const contents = []
        state.currentContentIds.forEach(id => {
            if (state.contents[id] !== undefined) {
                contents.push(state.contents[id])
            }
        })
        return contents
    },
    replies: state => content => {
        const replies = []
        state.contents[content.id].replyIds.forEach(id => {
            replies.push(state.contents[id])
        })
        return replies
    },
    shares: state => contentId => {
        const shares = []
        state.contents[contentId].shareIds.forEach(id => {
            shares.push(state.contents[id])
        })
        return shares
    },
    hasNewContent(state) {
        return state.unfetchedContentIds.length > 0 && !state.pending.contents
    },
}

export {streamActions, streamMutations, streamGetters}
