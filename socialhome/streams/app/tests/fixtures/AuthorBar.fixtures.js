import _ from "lodash/core"


const getAuthorBarPropsData = function (args = {}) {
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
        isUserAuthenticated: true,
    })
}

export {getAuthorBarPropsData}
