import _ from "lodash"
import faker from "faker"

const getFakeAuthor = function getFakeAuthor(args = {}) {
    return _.defaults({}, args, {
        uuid: faker.random.uuid(),
        handle: faker.internet.exampleEmail(),
        home_url: "https://127.0.0.1",
        id: faker.random.number(),
        image_url_small: "https://127.0.0.1/image.png",
        is_local: faker.random.boolean(),
        name: faker.name.findName(),
        url: "https://127.0.0.1",
        fid: `https://127.0.0.1/profile/${faker.random.uuid()}`,
        user_following: faker.random.boolean(),
    })
}

const getFakeContent = function getFakeContent(args = {}) {
    return _.defaults({}, args, {
        author: getFakeAuthor(),
        content_type: "content",
        edited: faker.random.boolean(),
        humanized_timestamp: faker.random.number(),
        id: faker.random.number(),
        parent: null,
        recipients: [],
        rendered: `<p>${faker.lorem.paragraphs()}</p>`,
        reply_count: faker.random.number(),
        replyIds: [],
        share_of: null,
        shareIds: [],
        shares_count: faker.random.number(),
        timestamp: faker.date.recent().toString(),
        url: "https://127.0.0.1",
        user_is_author: faker.random.boolean(),
        user_has_shared: faker.random.boolean(),
        visibility: "public",
        through_author: {},
    })
}

const getProfile = function getProfile(args = {}) {
    return _.defaults({}, args, {
        id: faker.random.number(),
        uuid: faker.random.uuid(),
        followersCount: faker.random.number(),
        followingCount: faker.random.number(),
        handle: faker.internet.exampleEmail(),
        saferImageUrlLarge: "https://127.0.0.1/image.png",
        streamType: "all_content",
        pinnedContentExists: faker.random.boolean(),
    })
}

const getContext = function getContext(args = {}) {
    return _.defaults({}, args, {
        currentBrowsingProfileId: faker.random.number(),
        streamName: "public",
        isUserAuthenticated: faker.random.boolean(),
        profile: getProfile(),
    })
}

export {getFakeAuthor, getFakeContent, getProfile, getContext}
