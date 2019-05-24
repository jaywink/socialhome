/* eslint-disable global-require */
const path = require("path")

module.exports = {
    configureWebpack: {
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
    css: {loaderOptions: {postcss: {plugins: [require("autoprefixer")({})]}}},
    outputDir: path.resolve(__dirname, "..", "static", "dist", "vue"),
}
