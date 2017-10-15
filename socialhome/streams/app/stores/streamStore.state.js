import _get from "lodash/get"
import _forEach from "lodash/forEach"


export default function () {
    const contentIds = []
    const contents = {}
    const streamName = _get(window, ["context", "streamName"], "")

    return {
        contents,
        contentIds,
        hasNewContent: false,
        newContentLengh: 0,
        showAuthorBar: streamName.length > 0 ? !streamName.startsWith("profile_") : false,
        streamName,
        tagName: _get(window, ["context", "tagName"], ""),
    }
}
