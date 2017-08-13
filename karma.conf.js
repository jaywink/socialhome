const wpConf = require("./webpack.config")

module.exports = config => {
    config.set({
        browsers: ["PhantomJS"],
        files: [
            {pattern: "./node_modules/babel-polyfill/dist/polyfill.js", watched: false},
            {pattern: "./socialhome/**/app/tests/**/*.tests.js", watched: false}
        ],
        frameworks: ["mocha"],
        plugins: [
            "karma-phantomjs-launcher",
            "karma-mocha",
            "karma-sourcemap-loader",
            "karma-webpack",
        ],
        preprocessors: {
            "./node_modules/babel-polyfill/dist/polyfill.js": ["webpack", "sourcemap"],
            "./socialhome/**/app/tests/**/*.tests.js": ["webpack", "sourcemap"]
        },
        reporters: ["dots"],
        singleRun: true,
        webpack: {
            module: wpConf.module,
            resolve: wpConf.resolve,
            devtool: "inline-source-map"
        },
        webpackMiddleware: {noInfo: true},
    })
}
