import _get from "lodash/get"
import _keyBy from "lodash/keyBy"


export default function () {
    const streamName = _get(window, ["context", "streamName"], "")
    return {
        contentList: _keyBy(_get(window, ["context", "contentList"], []), item => item.id),
        showAuthorBar: streamName.length > 0 ? !streamName.startsWith("profile_") : false,
        hasNewContent: false,
        newContentLengh: 0,
        streamName,
    }
}
