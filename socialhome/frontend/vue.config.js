/* eslint-disable global-require */
const path = require("path")

module.exports = {
    chainWebpack: config => {
        config.optimization.splitChunks(false)
    },
    configureWebpack: {
        output: {filename: "js/[name].js"},
        resolve: {
            alias: {
                "%": path.resolve(__dirname, "tests"),
                "%fixtures": path.resolve(__dirname, "tests", "unit", "fixtures"),
                "mock-socket": "mock-socket/dist/mock-socket.js",
                "reconnecting-websocket": "ReconnectingWebSocket/reconnecting-websocket.min.js",
                "vue-masonry": "vue-masonry/src/masonry.plugin.js",
                vue$: "vue/dist/vue.common.js",
            },
        },
    },
    css: {
        extract: false,
        loaderOptions: {postcss: {plugins: [require("autoprefixer")({})]}},
    },
    outputDir: path.resolve(__dirname, "..", "static", "dist", "vue"),
    pwa: {
        iconPaths: {
            favicon32: "static/images/logo/Socialhome-dark-16.png",
            favicon16: "static/images/logo/Socialhome-dark-32.png",
            appleTouchIcon: "static/images/logo/Socialhome-dark-300.png",
            maskIcon: "static/images/logo/Socialhome-dark.svg",
            msTileImage: "static/images/logo/Socialhome-light-300.png",
        },
    },
}
