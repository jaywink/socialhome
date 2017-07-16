const path = require("path")
const webpack = require("webpack")

module.exports = {
    entry: path.resolve(__dirname, "socialhome/streams/app/main.js"),
    output: {
        path: path.resolve(__dirname, "socialhome/static/js"),
        filename: "webpack.bundle.js"
    },
    module: {
        loaders: [
            {
                test: /.js$/,
                loader: "babel-loader",
                query: {
                    presets: ["es2017"]
                }
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
        alias: {
            vue: "vue/dist/vue.js"
        }
    },
    stats: {
        colors: true
    },
    devtool: "cheap-module-source-map"
}
