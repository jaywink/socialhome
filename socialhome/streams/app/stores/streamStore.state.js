import _get from "lodash/get"
import _forEach from "lodash/forEach"


export default function () {
    const contentIds = []
    const contents = {}
    _forEach(_get(window, ["context", "contentList"], []), content => {
        contentIds.push(content.id)
        contents[content.id] = content
    })

    const streamName = _get(window, ["context", "streamName"], "")

    return {
        contents,
        contentIds,
        showAuthorBar: streamName.length > 0 ? !streamName.startsWith("profile_") : false,
        hasNewContent: false,
        newContentLengh: 0,
        streamName,
    }
}
