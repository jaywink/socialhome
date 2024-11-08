/* eslint-disable import/no-dynamic-require,import/newline-after-import */
const path = require("path")
const HTML = `<!doctype html>
    <html lang="en">
        <head>
            <meta charset="utf-8">
            <title>Socialhome tests</title>
        </head>
        <body>
            <div id="app"></div>
        </body>
</html>`

require("jsdom-global")(HTML, {
    pretendToBeVisual: true, url: "http://localhost",
})
const jsdom = require("jsdom-global")
global.jsdom = new jsdom.JSDOM(HTML)
require("chai/register-should.js")
require("chai").use(require("chai-as-promised")).use(require("sinon-chai"))
// Django's gettext and other i18n functions
require("django-i18n")
const Sinon = require("sinon").createSandbox()

// Trap calls to global library `Urls`
const {Urls} = require(path.resolve(__dirname, "fixtures", "Urls.js"))
/* eslint-enable import/no-dynamic-require,import/newline-after-import */

// JSDOM fixes
// See https://github.com/jsdom/jsdom/issues/317
const createRange = () => ({
    setEnd: () => {},
    setStart: () => {},
    getBoundingClientRect: () => ({right: 0}),
    getClientRects: () => [],
    createContextualFragment: html => {
        const div = document.createElement("div")
        div.innerHTML = html
        return div.children[0]
    },
})

global.Urls = Urls
global.Sinon = Sinon
global.window.Date = Date
global.window.document.createRange = createRange
global.window.document.body.createTextRange = () => {}
global.window.focus = () => {}

// Noop function to make the tests pass
global.WebSocket = function () {} // eslint-disable-line func-names
// Absence of WebSocket.prototype.close can cause tests to randomly fail
// when components using websocket try to close socket
global.WebSocket.prototype.close = function () {} // eslint-disable-line func-names
