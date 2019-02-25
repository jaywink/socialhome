import _get from "lodash/get"


export default function () {
    const contentIds = []
    const unfetchedContentIds = []
    const contents = {}
    const replies = {}
    const shares = {}

    // Handle single content if exists
    const content = _get(window, ["context", "content"], undefined)
    let singleContentId = null
    if (content) {
        singleContentId = content.id
        content.replyIds = []
        content.shareIds = []
        contentIds.push(content.id)
        contents[content.id] = content
    }

    const streamName = _get(window, ["context", "streamName"], "")
    const streamSplits = streamName.split("__")
    const stream = {
        id: streamSplits.length ? streamSplits[1] : "",
        isProfile: streamName.startsWith("profile_"),
        name: streamSplits[0],
        single: streamSplits[0] === "content",
    }

    return {
        contents,
        contentIds,
        hasNewContent: false,
        layoutDoneAfterTwitterOEmbeds: false,
        newContentLengh: 0,
        replies,
        shares,
        showAuthorBar: !stream.isProfile,
        singleContentId,
        stream,
        streamName,
        tagName: _get(window, ["context", "tagName"], ""),
        unfetchedContentIds,
    }
}
