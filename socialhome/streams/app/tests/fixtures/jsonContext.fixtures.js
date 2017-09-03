import _ from "lodash"
import faker from "faker"


const getFakeAuthor = function (args = {}) {
    return _.defaults({}, args, {
        guid: faker.random.uuid(),
        name: faker.name.findName(),
        handle: faker.internet.exampleEmail(),
        imageUrlSmall: "https://127.0.0.1/image.png",
        absoluteUrl: "https://127.0.0.1",
        homeUrl: "https://127.0.0.1",
        isUserFollowingAuthor: faker.random.boolean(),
    })
}

const getFakePost = function (args = {}) {
    return _.defaults({}, args, {
        htmlSafe: `<p>${faker.lorem.paragraphs()}</p>`,
        id: faker.random.number(),
        author: getFakeAuthor(),
        timestamp: faker.date.recent().toString(),
        humanizedTimestamp: faker.date.recent().toString(),
        edited: faker.random.boolean(),
        repliesCount: faker.random.number(),
        sharesCount: faker.random.number(),
        isUserLocal: faker.random.boolean(),
        isUserAuthor: faker.random.boolean(),
        contentUrl: "https://127.0.0.1",
        hasShared: faker.random.boolean(),
    })
}

const getContextWithFakePosts = function (args = {}, nbPosts = 1) {
    let contentList = []
    for(let n = 0; ++n <= nbPosts;){
        contentList.push(getFakePost())
    }
    args.contentList = _.concat(contentList, _.get(args, ["contentList"], []))

    return _.defaults({}, args, {
        currentBrowsingProfileId: faker.random.number(),
        streamName: "public",
        isUserAuthenticated: faker.random.boolean()
    })
}

export {getFakeAuthor, getFakePost, getContextWithFakePosts}
