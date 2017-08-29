import _ from "lodash/core"
import faker from "faker"

const getReactionsBarPropsData = function (args = {}) {
    return _.defaults({}, args, {
        id: faker.random.number(),
        repliesCount: faker.random.number(),
        sharesCount: faker.random.number(),
        hasShared: faker.random.boolean()
    })
}

export {getReactionsBarPropsData}
