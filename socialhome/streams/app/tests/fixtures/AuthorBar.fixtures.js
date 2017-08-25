import _ from "lodash/core"
import faker from "faker"


const getAuthorBarPropsData = function (args = {}) {
    return _.defaults({}, args, {
        handle: faker.internet.email(),
        name: faker.name.findName(),
        guid: `${faker.random.number()}`,
        homeUrl: "https://127.0.0.1",
        absoluteUrl: "https://127.0.0.1",
        imageUrlSmall: "https://127.0.0.1",
        isUserAuthor: true,
        isUserLocal: true,
        isUserFollowingAuthor: true,
    })
}

export {getAuthorBarPropsData}
