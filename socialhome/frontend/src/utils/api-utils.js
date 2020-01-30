import {snakeCase} from "snake-case"
import _isArray from "lodash/isArray"

function mapParams(params = {}, snake = false) {
    Object.entries(params)
        // eslint-disable-next-line no-unused-vars
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => {
            if (_isArray(value)) return `${key}=${value.join(",")}`
            return snake ? snakeCase(value.toString()) : value.toString()
        })
        .reduce((previousValue, currentValue) => `${previousValue}&${currentValue}`, "?")
}

// eslint-disable-next-line import/prefer-default-export
export {mapParams}
