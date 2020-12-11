import _get from "lodash/get"

export default function () {
    // The top level content ID's loaded into the stream
    const currentContentIds = []
    // All content objects, including replies
    const allContentIds = []
    const unfetchedContentIds = []
    const contents = {}

    // Handle single content if exists
    const content = _get(window, ["context", "content"], undefined)
    let singleContentId = null
    if (content) {
        singleContentId = content.id
        content.replyIds = []
        content.shareIds = []
        currentContentIds.push(content.id)
        allContentIds.push(content.id)
        contents[content.id] = content
    }

    const streamName = _get(window, ["context", "streamName"], "")
    const streamSplits = streamName.split("__")
    const stream = {
        id: streamSplits.length ? streamSplits[1] : "",
        name: streamSplits[0],
        single: streamSplits[0] === "content",
    }
    // Only defined if on a tag stream
    const tagContext = _get(window, ["context", "tag"], {})
    const tag = {
        name: tagContext.name,
        uuid: tagContext.uuid,
    }

    return {
        contents,
        currentContentIds,
        allContentIds,
        hasNewContent: false,
        layoutDoneAfterTwitterOEmbeds: false,
        newContentLengh: 0,
        showAuthorBar: stream.name !== "profile_pinned",
        singleContentId,
        stream,
        streamName,
        tag,
        unfetchedContentIds,
    }
}
