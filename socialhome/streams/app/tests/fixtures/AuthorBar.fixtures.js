import _ from "lodash/core"

const getPropsData = function (args = {}) {
    return _.defaults({}, args, {
        handle: "",
        name: "",
        guid: "",
        currentBrowsingProfileId: "",
        homeUrl: "",
        absoluteUrl: "",
        imageUrlSmall: "",
        isUserAuthor: true,
        isUserLocal: true,
        isUserFollowingAuthor: true,
        isUserAuthentificated: true,
    })
}

export {getPropsData}
