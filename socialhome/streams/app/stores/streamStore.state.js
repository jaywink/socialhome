import _get from "lodash/get"


export default function () {
    const contentIds = []
    const unfetchedContentIds = []
    const contents = {}
    const replies = {}
    const shares = {}
    const streamName = _get(window, ["context", "streamName"], "")

    return {
        contents,
        contentIds,
        hasNewContent: false,
        newContentLengh: 0,
        replies,
        shares,
        showAuthorBar: streamName.length > 0 ? !streamName.startsWith("profile_") : false,
        streamName,
        tagName: _get(window, ["context", "tagName"], ""),
        unfetchedContentIds,
    }
}
