const path = require("path")
const webpack = require("webpack")

module.exports = {
    entry: {
        stream: path.resolve(__dirname, "socialhome/streams/app/main.js")
    },
    output: {
        path: path.resolve(__dirname, "socialhome/static/js"),
        filename: "webpack.[name].js"
    },
    module: {
        loaders: [
            {
                test: /.js$/,
                loader: "babel-loader",
                exclude: /node_modules/,
                query: {presets: ["es2017"]}
            },
            {
                test: /\.scss$/,
                loaders: ["css-loader", "sass-loader"]
            },
            {
                test: /\.vue$/,
                loader: "vue-loader",
                options: {
                    loaders: {
                        scss: ["vue-style-loader", "css-loader", "sass-loader"],
                        js: "babel-loader"
                    }
                }
            }
        ]
    },
    resolve: {
        modules: [
            path.resolve(__dirname, "socialhome"),
            path.resolve(__dirname, "node_modules")
        ],
        alias: {vue: "vue/dist/vue.js",}
    },
    stats: {colors: true},
    devtool: "cheap-module-source-map"
}
