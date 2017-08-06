const wpConf = require("./webpack.config")
wpConf.devtool = "inline-source-map"

module.exports = config => {
    config.set({
        browsers:      ["PhantomJS"],
        files:         ["./socialhome/**/app/tests/**/*\.tests\.js"],
        frameworks:    ["mocha"],
        plugins:       [
            "karma-phantomjs-launcher",
            "karma-mocha",
            "karma-sourcemap-loader",
            "karma-webpack"
        ],
        preprocessors: {"./socialhome/**/app/tests/**/*\.tests\.js": ["webpack", "sourcemap"]},
        reporters:     ["dots"],
        singleRun:     true,
        webpack:       wpConf
    })
}
