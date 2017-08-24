import _ from "lodash/core"
import faker from "faker"

import {getAuthorBarPropsData} from "streams/app/tests/fixtures/AuthorBar.fixtures";


const getStreamElementPropsData = function (args = {}) {
    return _.defaults({}, args, {
        id: faker.random.number(),
        author: getAuthorBarPropsData(),
        timestamp: faker.date.recent().toString(),
        humanizedTimestamp: faker.date.recent().toString(),
        htmlSafe: faker.lorem.paragraphs(),
        contentUrl: "https://127.0.0.1",
        updateUrl: "https://127.0.0.1",
        deleteUrl: "https://127.0.0.1",
        replyUrl: "https://127.0.0.1",
        childrenCount: faker.random.number(),
        sharesCount: faker.random.number(),
        edited: faker.random.boolean(),
        isUserLocal: faker.random.boolean(),
        isUserAuthor: faker.random.boolean(),
        showAuthorBar: faker.random.boolean(),
        isUserAuthenticated: faker.random.boolean(),
        currentBrowsingProfileId: faker.random.number().toString(),
    })
}

export {getStreamElementPropsData}
