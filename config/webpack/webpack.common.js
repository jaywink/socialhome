const path = require("path")

module.exports = {
    entry: {
        stream: path.resolve(__dirname, "../../socialhome/streams/app/main.js"),
    },
    output: {
        path: path.resolve(__dirname, "../../socialhome/static/js"),
        filename: "webpack.[name].js",
    },
    module: {
        loaders: [
            {
                test: /\.js$/,
                loader: "babel-loader",
                include: [
                    path.resolve(__dirname, "../../socialhome"),
                    path.resolve(__dirname, "../../mocha"),
                ],
                exclude: path.resolve(__dirname, "../../socialhome/static/js"),
                query: {presets: ["env"]},
            },
            {
                test: /\.scss$/,
                loaders: ["css-loader", "sass-loader"],
            },
            {
                test: /\.vue$/,
                loader: "vue-loader",
                options: {
                    loaders: {
                        scss: ["vue-style-loader", "css-loader", "sass-loader"],
                        js: "babel-loader",
                    },
                },
            },
        ],
    },
    resolve: {
        modules: [
            path.resolve(__dirname, "../../socialhome"),
            path.resolve(__dirname, "../../node_modules"),
        ],
        alias: {
            "bootstrap-vue": "bootstrap-vue/dist/bootstrap-vue.esm.js",
            "mock-socket": "mock-socket/dist/mock-socket.js",
            "reconnecting-websocket": "ReconnectingWebSocket/reconnecting-websocket.min.js",
            vue$: "vue/dist/vue.esm.js",
        },
        extensions: [".webpack.js", ".js", ".vue"],
    },
    stats: {colors: true},
}
