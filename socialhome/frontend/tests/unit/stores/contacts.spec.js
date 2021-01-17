import Vuex from "vuex"
import Moxios from "moxios"
import {createLocalVue} from "@vue/test-utils"
import initVue from "@/init-vue"
import getContactsStore from "@/store/modules/contacts"

import {getContactsFollowersResponse, getContactsFollowingResponse} from "%fixtures/contacts.fixtures"

const localVue = createLocalVue()
initVue(localVue)
localVue.use(Vuex)

describe("contacts", () => {
    beforeEach(() => {
        Sinon.restore()
        Moxios.install(localVue.axios)
    })

    afterEach(() => {
        Moxios.uninstall()
    })

    describe("contactsFollowers", () => {
        it("should query the followers API endpoint", done => {
            const target = new Vuex.Store(getContactsStore(localVue.axios))

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/profiles/followers/")
                done()
            })

            target.dispatch("contactsFollowers").catch(done)
        })

        it("should query the followers API endpoint with page_size parameter", done => {
            const target = new Vuex.Store(getContactsStore(localVue.axios))

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/profiles/followers/?page_size=2000")
                done()
            })

            target.dispatch("contactsFollowers", {params: {pageSize: 2000}}).catch(done)
        })

        it("should query the followers API endpoint with page parameter", done => {
            const target = new Vuex.Store(getContactsStore(localVue.axios))

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/profiles/followers/?page=2")
                done()
            })

            target.dispatch("contactsFollowers", {params: {page: 2}}).catch(done)
        })

        it("should query the followers API endpoint with page and page_size parameter", done => {
            const target = new Vuex.Store(getContactsStore(localVue.axios))

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/profiles/followers/?page=2&page_size=2000")
                done()
            })

            target.dispatch("contactsFollowers", {
                params: {
                    page: 2, pageSize: 2000,
                },
            }).catch(done)
        })

        it("should update the state after success", async () => {
            const target = new Vuex.Store(getContactsStore(localVue.axios))
            const contactResponse = getContactsFollowersResponse()

            Moxios.wait(() => {
                Moxios.requests.mostRecent().respondWith({
                    status: 200,
                    response: contactResponse,
                })
            })

            await target.dispatch("contactsFollowers")
            target.state.followers.should.eql({
                count: 3,
                next: "2",
                contacts: contactResponse.results,
            })
        })
    })

    describe("contactsFollowing", () => {
        it("should query the followers API endpoint", done => {
            const target = new Vuex.Store(getContactsStore(localVue.axios))

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/profiles/following/")
                done()
            })

            target.dispatch("contactsFollowing").catch(done)
        })

        it("should query the followers API endpoint with page_size parameter", done => {
            const target = new Vuex.Store(getContactsStore(localVue.axios))

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/profiles/following/?page_size=2000")
                done()
            })

            target.dispatch("contactsFollowing", {params: {pageSize: 2000}}).catch(done)
        })

        it("should query the followers API endpoint with page parameter", done => {
            const target = new Vuex.Store(getContactsStore(localVue.axios))

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/profiles/following/?page=2")
                done()
            })

            target.dispatch("contactsFollowing", {params: {page: 2}}).catch(done)
        })

        it("should query the followers API endpoint with page and page_size parameter", done => {
            const target = new Vuex.Store(getContactsStore(localVue.axios))

            Moxios.wait(() => {
                const request = Moxios.requests.mostRecent()
                request.url.should.eql("/api/profiles/following/?page=2&page_size=2000")
                done()
            })

            target.dispatch("contactsFollowing", {
                params: {
                    page: 2, pageSize: 2000,
                },
            }).catch(done)
        })

        it("should update the state after success", async () => {
            const target = new Vuex.Store(getContactsStore(localVue.axios))
            const contactResponse = getContactsFollowingResponse()

            Moxios.stubRequest("/api/profiles/following/", {
                status: 200,
                response: contactResponse,
            })

            await target.dispatch("contactsFollowing")

            target.state.following.should.eql({
                count: 3,
                next: "2",
                contacts: contactResponse.results,
            })
        })
    })
})
