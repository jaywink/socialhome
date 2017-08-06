const wpConf = require("./webpack.config")
wpConf.devtool = "inline-source-map"

module.exports = config => {
    let findTests = () => {
        // THIS is why I hate NodeJS. That tool is so immature that you always
        // have to install a bunch of crappy modules to do some tiny operation
        // Long life to Python \o/
        let glob = require("glob")
        return glob.sync("./socialhome/**/app/tests/**/*\.tests\.js")
    }

    let preprocessors = () => {
        let result = {}
        for (let file of findTests()) {
            result[`${file}`] = ["webpack", "sourcemap"]
        }
        return result
    }

    config.set({
        browsers:      ["PhantomJS"],
        files:         findTests(),
        frameworks:    ["mocha"],
        plugins:       [
            "karma-phantomjs-launcher",
            "karma-mocha",
            "karma-sourcemap-loader",
            "karma-webpack"
        ],
        preprocessors: preprocessors(),
        reporters:     ["dots"],
        singleRun:     true,
        webpack:       wpConf
    })
}
