import _ from "lodash"
import faker from "faker"

const getFakeAuthor = function getFakeAuthor(args = {}) {
    return _.defaults({}, args, {
        uuid: faker.datatype.uuid(),
        handle: faker.internet.exampleEmail(),
        home_url: "https://127.0.0.1",
        id: faker.datatype.number(),
        image_url_small: "https://127.0.0.1/image.png",
        is_local: faker.datatype.boolean(),
        name: faker.name.findName(),
        url: "https://127.0.0.1",
        fid: `https://127.0.0.1/profile/${faker.datatype.uuid()}`,
        user_following: faker.datatype.boolean(),
    })
}

const getFakeContent = function getFakeContent(args = {}) {
    return _.defaults({}, args, {
        author: getFakeAuthor(),
        content_type: "content",
        edited: faker.datatype.boolean(),
        humanized_timestamp: faker.datatype.number(),
        id: faker.datatype.number(),
        parent: null,
        recipients: [],
        rendered: `<p>${faker.lorem.paragraphs()}</p>`,
        reply_count: faker.datatype.number(),
        replyIds: [],
        share_of: null,
        shareIds: [],
        shares_count: faker.datatype.number(),
        timestamp: faker.date.recent().toString(),
        url: "https://127.0.0.1",
        user_is_author: faker.datatype.boolean(),
        user_has_shared: faker.datatype.boolean(),
        visibility: "public",
        through_author: {},
    })
}

const getProfile = function getProfile(args = {}) {
    return _.defaults({}, args, {
        id: faker.datatype.number(),
        uuid: faker.datatype.uuid(),
        followersCount: faker.datatype.number(),
        followingCount: faker.datatype.number(),
        handle: faker.internet.exampleEmail(),
        saferImageUrlLarge: "https://127.0.0.1/image.png",
        streamType: "all_content",
        pinnedContentExists: faker.datatype.boolean(),
    })
}

const getContext = function getContext(args = {}) {
    return _.defaults({}, args, {
        currentBrowsingProfileId: faker.datatype.number(),
        streamName: "public",
        isUserAuthenticated: faker.datatype.boolean(),
        profile: getProfile(),
    })
}

export {getFakeAuthor, getFakeContent, getProfile, getContext}
