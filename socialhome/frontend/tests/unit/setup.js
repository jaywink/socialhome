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
