import _ from "lodash/core"
import faker from "faker"


const getAuthorBarPropsData = function (args = {}) {
    return _.defaults({}, args, {
        handle: faker.internet.exampleEmail(),
        name: faker.name.findName(),
        guid: faker.random.uuid(),
        homeUrl: "https://127.0.0.1",
        absoluteUrl: "https://127.0.0.1",
        imageUrlSmall: "https://127.0.0.1/image.png",
        isUserAuthor: true,
        isUserLocal: true,
        isUserFollowingAuthor: true,
    })
}

export {getAuthorBarPropsData}
