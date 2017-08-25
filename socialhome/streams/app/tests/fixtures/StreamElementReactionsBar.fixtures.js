import _ from "lodash/core"
import faker from "faker"

import {getAuthorBarPropsData} from "streams/app/tests/fixtures/AuthorBar.fixtures";


const getStreamElementReactionsBarPropsData = function (args = {}) {
    return _.defaults({}, args, {
        id: faker.random.number(),
        repliesCount: faker.random.number(),
        sharesCount: faker.random.number(),
    })
}

export {getStreamElementReactionsBarPropsData}
