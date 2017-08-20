import _isNumber from "lodash/isNumber"
import _get from "lodash/get"


export default function () {
    return {
        translations: {
            stampedContent: {
                h2: _get(window, ["context", "translations", "stampedContent", "h2"], ""),
                p: _get(window, ["context", "translations", "stampedContent", "p"], ""),
            },
        },
        contentList: _get(window, ["context", "contentList"], []),
        stream: {
            hasNewContent: false,
            newContentLengh: 0,
            streamName: _get(window, ["context", "streamName"], ""),
        },
        isUserAuthenticated: _get(window, ["context", "isUserAuthenticated"], false),
        showAuthorBar: _get(window, ["context", "showAuthorBar"], false),
        currentBrowsingProfileId: (_isNumber(_get(window, ["context", "currentBrowsingProfileId"], undefined))
            ? `${window.context.currentBrowsingProfileId}` : undefined),
    }
}
