import "streams/app/main"

import Vue from "vue"


describe("Main", () => {
    it("should initialize Axios library with correct parameters", () => {
        Vue.prototype.$http.should.exist
        Vue.prototype.$http.defaults.xsrfCookieName.should.equal("csrftoken")
        Vue.prototype.$http.defaults.xsrfHeaderName.should.equal("X-CSRFToken")
    })

    it("Vue.redrawVueMasonry is defined", () => {
        (typeof Vue.redrawVueMasonry).should.equal("function")
    })
})
