const path = require("path")
const ExtractTextPlugin = require("extract-text-webpack-plugin")

module.exports = {
    entry: path.resolve(__dirname, "../../socialhome/frontend/main.js"),
    output: {
        path: path.resolve(__dirname, "../../socialhome/static/dist"),
        filename: "webpack.bundle.js",
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
                query: {presets: ["vue-app"]},
            },
            {
                test: /\.scss$/,
                use: ExtractTextPlugin.extract({
                    fallback: "style-loader",
                    use: ["css-loader", "sass-loader"],
                }),
            },
            {
                test: /\.css$/,
                use: ExtractTextPlugin.extract({
                    fallback: "style-loader",
                    use: "css-loader",
                }),
            },
            {
                test: /\.vue$/,
                loader: "vue-loader",
                options: {
                    loaders: {
                        scss: ExtractTextPlugin.extract({
                            use: ["css-loader", "sass-loader"],
                            fallback: "vue-style-loader",
                        }),
                        js: "babel-loader",
                    },
                },
            },
            {
                test: /\.(eot|woff|woff2|svg|ttf)$/,
                use: ["file-loader"]
            },
        ],
    },
    plugins: [
        new ExtractTextPlugin("webpack.bundle.css"),
    ],
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
