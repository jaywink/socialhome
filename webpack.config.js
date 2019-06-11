// This file is for helping IntelliJ with module import auto-completion.
// IntelliJ looks for this file at the root of the project and detects WP configuration.
const path = require("path")

const cwd = process.cwd()
process.chdir(path.resolve(__dirname, "socialhome", "frontend"))
const wpconf = require("./socialhome/frontend/node_modules/@vue/cli-service/webpack.config.js")

process.chdir(cwd)
module.exports = wpconf
