import Moxios from "moxios"
import Vue from "vue"
import Vuex from "vuex"
import Axios from "axios"
import VueSnotify from "vue-snotify"
import uuid from "uuid"

import {getFakeContent} from "frontend/tests/fixtures/jsonContext.fixtures"
import getState from "frontend/store/modules/stream.state"
import {
    addHasLoadMore,
    fetchContentsSuccess,
    fetchNewContentSuccess,
    fetchRepliesSuccess,
    fetchSharesSuccess, newRestAPI, onError, mutations, actions, getters,
} from "../../store/modules/stream"

Vue.use(Vuex)

const UUID = uuid()

describe("streamStore", () => {
    afterEach(() => {
        Sinon.restore()
    })

    describe("addHasLoadMore", () => {
        it("adds flag on fifth last content", () => {
            const state = {contentIds: [...new Array(7).keys()].map(i => i), contents: {}}
            state.contentIds.forEach(id => {
                state.contents[id] = getFakeContent({id: id, hasLoadMore: false})
            })
            addHasLoadMore(state)
            state.contents[state.contentIds[0]].hasLoadMore.should.be.false
            state.contents[state.contentIds[1]].hasLoadMore.should.be.true
            state.contents[state.contentIds[2]].hasLoadMore.should.be.false
            state.contents[state.contentIds[3]].hasLoadMore.should.be.false
            state.contents[state.contentIds[4]].hasLoadMore.should.be.false
            state.contents[state.contentIds[5]].hasLoadMore.should.be.false
            state.contents[state.contentIds[6]].hasLoadMore.should.be.false
        })

        it("adds flag to last if under 5 contents", () => {
            const state = {contentIds: [...new Array(4).keys()].map(i => i), contents: {}}
            state.contentIds.forEach(id => {
                state.contents[id] = getFakeContent({id: id, hasLoadMore: false})
            })
            addHasLoadMore(state)
            state.contents[state.contentIds[0]].hasLoadMore.should.be.false
            state.contents[state.contentIds[1]].hasLoadMore.should.be.false
            state.contents[state.contentIds[2]].hasLoadMore.should.be.false
            state.contents[state.contentIds[3]].hasLoadMore.should.be.true
        })

        it("sets layoutDoneAfterTwitterOEmbeds to false", () => {
            const state = {
                contentIds: [...new Array(7).keys()].map(i => i),
                contents: {},
                layoutDoneAfterTwitterOEmbeds: true,
            }
            state.contentIds.forEach(id => {
                state.contents[id] = getFakeContent({id: id, hasLoadMore: false})
            })
            addHasLoadMore(state)
            state.layoutDoneAfterTwitterOEmbeds.should.be.false
        })
    })

    describe("fetchContentsSuccess", () => {
        it("should append payload to state", () => {
            let payload = {
                data: [
                    {id: "6", text: "foobar", content_type: "content"},
                    {id: "7", text: "blablabla", content_type: "content"},
                ],
            }

            let state = {
                contentIds: ["1", "2"],
                contents: {
                    "1": {id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: []},
                    "2": {id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: []},
                },
                replies: {},
                shares: {},
            }

            fetchContentsSuccess(state, payload)

            state.should.eql({
                contentIds: ["1", "2", "6", "7"],
                contents: {
                    "1": {id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: []},
                    "2": {id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: []},
                    "6": {id: "6", text: "foobar", content_type: "content", replyIds: [], shareIds: []},
                    "7": {
                        id: "7",
                        text: "blablabla",
                        content_type: "content",
                        replyIds: [],
                        shareIds: [],
                        hasLoadMore: true,
                    },
                },
                replies: {},
                shares: {},
                layoutDoneAfterTwitterOEmbeds: false,
            })
        })
    })

    describe("fetchRepliesSuccess", () => {
        it("should append array payload to state", () => {
            let payload = {
                data: [
                    {id: "6", text: "foobar", content_type: "reply", parent: "1"},
                    {id: "7", text: "blablabla", content_type: "reply", parent: "3"},
                ],
            }

            let state = {
                contents: {
                    "1": {id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: ["3"]},
                    "2": {id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: []},
                },
                replies: {},
                shares: {
                    "3": {id: "3", content_type: "share", share_of: "1", replyIds: []},
                },
            }

            fetchRepliesSuccess(state, payload)

            state.should.eql({
                contents: {
                    "1": {id: "1", text: "Plop", content_type: "content", replyIds: ["6"], shareIds: ["3"]},
                    "2": {id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: []},
                },
                replies: {
                    "6": {id: "6", text: "foobar", content_type: "reply", parent: "1", replyIds: [], shareIds: []},
                    "7": {id: "7", text: "blablabla", content_type: "reply", parent: "3", replyIds: [], shareIds: []},
                },
                shares: {
                    "3": {id: "3", content_type: "share", share_of: "1", replyIds: ["7"]},
                },
            })
        })

        it("should append single item payload to state", () => {
            let payload = {
                data: {id: "6", text: "foobar", content_type: "reply", parent: "1"},
            }

            let state = {
                contents: {
                    "1": {id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: ["3"]},
                    "2": {id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: []},
                },
                replies: {},
                shares: {
                    "3": {id: "3", content_type: "share", share_of: "1", replyIds: []},
                },
            }

            fetchRepliesSuccess(state, payload)

            state.should.eql({
                contents: {
                    "1": {id: "1", text: "Plop", content_type: "content", replyIds: ["6"], shareIds: ["3"]},
                    "2": {id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: []},
                },
                replies: {
                    "6": {id: "6", text: "foobar", content_type: "reply", parent: "1", replyIds: [], shareIds: []},
                },
                shares: {
                    "3": {id: "3", content_type: "share", share_of: "1", replyIds: []},
                },
            })
        })
    })

    describe("fetchSharesSuccess", () => {
        it("should append payload to state", () => {
            let payload = {
                data: [
                    {id: "6", content_type: "share", share_of: "1"},
                    {id: "7", content_type: "share", share_of: "2"},
                ],
            }

            let state = {
                contents: {
                    "1": {id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: []},
                    "2": {id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: []},
                },
                replies: {},
                shares: {},
            }

            fetchSharesSuccess(state, payload)

            state.should.eql({
                contents: {
                    "1": {id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: ["6"]},
                    "2": {id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: ["7"]},
                },
                replies: {},
                shares: {
                    "6": {id: "6", content_type: "share", share_of: "1", replyIds: []},
                    "7": {id: "7", content_type: "share", share_of: "2", replyIds: []},
                },
            })
        })
    })

    describe("fetchNewContentSuccess", () => {
        it("should append fetched content to contents", () => {
            let payload = {data: {id: "6", text: "Yolo"}}

            let state = {
                contents: {
                    "1": {id: "1", text: "Plop"},
                    "2": {id: "2", text: "Hello!"},
                },
                unfetchedContentIds: ["6"],
            }

            fetchNewContentSuccess(state, payload)

            state.contents.should.eql({
                "1": {id: "1", text: "Plop"},
                "2": {id: "2", text: "Hello!"},
                "6": {id: "6", text: "Yolo"},
            })
        })
    })

    describe("onError", () => {
        beforeEach(() => {
            Vue.use(VueSnotify)
            Vue.snotify = new Vue({}).$snotify
        })

        it("should log an error", () => {
            Sinon.spy(Vue.snotify, "error")
            onError({}, "unknown error")
            Vue.snotify.error.getCall(0).args[0].should.eq("An error happened while fetching new content")
        })
    })

    describe("newRestAPI", () => {
        let response
        let state
        let target

        beforeEach(() => {
            Moxios.install()
            state = getState()
            response = {
                status: 200,
                response: [
                    {id: "6", text: "foobar"},
                    {id: "7", text: "blablabla"},
                ],
            }
            target = new Vuex.Store(newRestAPI({state, baseURL: "", axios: Axios}))
        })

        afterEach(() => {
            Moxios.uninstall()
        })

        context("when requesting public stream", () => {
            beforeEach(() => {
                state.stream = {name: "public"}
            })

            it("should handle public stream request", (done) => {
                Moxios.stubRequest("/api/streams/public/", response)

                target.dispatch("getPublicStream", {params: {}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "6": {id: "6", text: "foobar", replyIds: [], shareIds: []},
                        "7": {id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true},
                    })
                    done()
                })
            })

            it("should handle public stream request with lastId", (done) => {
                Moxios.stubRequest("/api/streams/public/?last_id=8", response)

                target.dispatch("getPublicStream", {params: {lastId: 8}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "6": {id: "6", text: "foobar", replyIds: [], shareIds: []},
                        "7": {id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true},
                    })
                    done()
                })
            })

            it("should handle public stream request error", (done) => {
                Moxios.stubRequest("/api/streams/public/", {status: 500})

                target.dispatch("getPublicStream", {params: {}})

                Moxios.wait(() => {
                    target.state.error.contents.should.exist
                    target.state.contents.should.eql({})
                    done()
                })
            })
        })

        context("when requesting followed stream", () => {
            beforeEach(() => {
                state.stream = {name: "followed"}
            })

            it("should handle followed stream request", (done) => {
                Moxios.stubRequest("/api/streams/followed/", response)

                target.dispatch("getFollowedStream", {params: {}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "6": {id: "6", text: "foobar", replyIds: [], shareIds: []},
                        "7": {id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true},
                    })
                    done()
                })
            })

            it("should handle followed stream request with lastId", (done) => {
                Moxios.stubRequest("/api/streams/followed/?last_id=8", response)

                target.dispatch("getFollowedStream", {params: {lastId: 8}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "6": {id: "6", text: "foobar", replyIds: [], shareIds: []},
                        "7": {id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true},
                    })
                    done()
                })
            })

            it("should handle followed stream request error", (done) => {
                Moxios.stubRequest("/api/streams/followed/", {status: 500})

                target.dispatch("getFollowedStream", {params: {}})

                Moxios.wait(() => {
                    target.state.error.contents.should.exist
                    target.state.contents.should.eql({})
                    done()
                })
            })
        })

        context("when requesting tag stream", () => {
            beforeEach(() => {
                state.stream = {name: "tag", id: "yolo"}
            })

            it("should handle tag stream request", (done) => {
                Moxios.stubRequest("/api/streams/tag/yolo/", response)

                target.dispatch("getTagStream", {params: {name: "yolo"}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "6": {id: "6", text: "foobar", replyIds: [], shareIds: []},
                        "7": {id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true},
                    })
                    done()
                })
            })

            it("should handle tag stream request with lastId", (done) => {
                Moxios.stubRequest("/api/streams/tag/yolo/?last_id=8", response)

                target.dispatch("getTagStream", {params: {name: "yolo", lastId: 8}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "6": {id: "6", text: "foobar", replyIds: [], shareIds: []},
                        "7": {id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true},
                    })
                    done()
                })
            })

            it("should handle tag stream request error", (done) => {
                Moxios.stubRequest("/api/streams/tag/yolo/", {status: 500})

                target.dispatch("getTagStream", {params: {name: "yolo"}})

                Moxios.wait(() => {
                    target.state.error.contents.should.exist
                    target.state.contents.should.eql({})
                    done()
                })
            })
        })

        context("when requesting profile all stream", () => {
            beforeEach(() => {
                state.stream = {name: "profile_all"}
            })

            it("should handle profile stream request", (done) => {
                Moxios.stubRequest("/api/streams/profile-all/" + UUID + "/", response)

                target.dispatch("getProfileAll", {params: {uuid: UUID}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "6": {id: "6", text: "foobar", replyIds: [], shareIds: []},
                        "7": {id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true},
                    })
                    done()
                })
            })

            it("should handle profile all stream request with lastId", (done) => {
                Moxios.stubRequest("/api/streams/profile-all/" + UUID + "/?last_id=8", response)

                target.dispatch("getProfileAll", {params: {uuid: UUID, lastId: 8}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "6": {id: "6", text: "foobar", replyIds: [], shareIds: []},
                        "7": {id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true},
                    })
                    done()
                })
            })

            it("should handle profile stream request error", (done) => {
                Moxios.stubRequest("/api/streams/profile-all/" + UUID + "/", {status: 500})

                target.dispatch("getProfileAll", {params: {uuid: UUID}})

                Moxios.wait(() => {
                    target.state.error.contents.should.exist
                    target.state.contents.should.eql({})
                    done()
                })
            })
        })

        context("when requesting profile pinned stream", () => {
            beforeEach(() => {
                state.stream = {name: "profile_pinned"}
            })

            it("should handle profile stream request", (done) => {
                Moxios.stubRequest("/api/streams/profile-pinned/" + UUID + "/", response)

                target.dispatch("getProfilePinned", {params: {uuid: UUID}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "6": {id: "6", text: "foobar", replyIds: [], shareIds: []},
                        "7": {id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true},
                    })
                    done()
                })
            })

            it("should handle profile pinned stream request with lastId", (done) => {
                Moxios.stubRequest("/api/streams/profile-pinned/" + UUID + "/?last_id=8", response)

                target.dispatch("getProfilePinned", {params: {uuid: UUID, lastId: 8}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "6": {id: "6", text: "foobar", replyIds: [], shareIds: []},
                        "7": {id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true},
                    })
                    done()
                })
            })

            it("should handle profile stream request error", (done) => {
                Moxios.stubRequest("/api/streams/profile-pinned/" + UUID + "/", {status: 500})

                target.dispatch("getProfilePinned", {params: {uuid: UUID}})

                Moxios.wait(() => {
                    target.state.error.contents.should.exist
                    target.state.contents.should.eql({})
                    done()
                })
            })
        })

        context("when requesting replies", () => {
            it("should handle request", (done) => {
                Vue.set(target.state.contents, "1", {id: "1", text: "content", replyIds: [], shareIds: []})
                Moxios.stubRequest("/api/content/1/replies/", {
                    status: 200,
                    response: [
                        {id: "6", text: "foobar", content_type: "reply", parent: "1"},
                        {id: "7", text: "blablabla", content_type: "reply", parent: "1"},
                    ],
                })

                target.dispatch("getReplies", {params: {id: 1}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "1": {id: "1", text: "content", replyIds: ["6", "7"], shareIds: []},
                    })
                    target.state.replies.should.eql({
                        "6": {id: "6", text: "foobar", content_type: "reply", parent: "1", replyIds: [], shareIds: []},
                        "7": {
                            id: "7", text: "blablabla", content_type: "reply", parent: "1", replyIds: [], shareIds: [],
                        },
                    })
                    done()
                })
            })

            it("should handle error", (done) => {
                Moxios.stubRequest("/api/content/1/replies/", {status: 500})

                target.dispatch("getReplies", {params: {id: 1}})

                Moxios.wait(() => {
                    target.state.error.replies.should.exist
                    target.state.replies.should.eql({})
                    done()
                })
            })
        })

        context("when requesting shares", () => {
            it("should handle request", (done) => {
                Vue.set(target.state.contents, "1", {id: "1", text: "content", replyIds: [], shareIds: []})
                Moxios.stubRequest("/api/content/1/shares/", {
                    status: 200,
                    response: [
                        {id: "6", content_type: "share", share_of: "1"},
                        {id: "7", content_type: "share", share_of: "1"},
                    ],
                })

                target.dispatch("getShares", {params: {id: 1}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "1": {id: "1", text: "content", replyIds: [], shareIds: ["6", "7"]},
                    })
                    target.state.shares.should.eql({
                        "6": {id: "6", content_type: "share", share_of: "1", replyIds: []},
                        "7": {id: "7", content_type: "share", share_of: "1", replyIds: []},
                    })
                    done()
                })
            })

            it("should handle error", (done) => {
                Moxios.stubRequest("/api/content/1/shares/", {status: 500})

                target.dispatch("getShares", {params: {id: 1}})

                Moxios.wait(() => {
                    target.state.error.shares.should.exist
                    target.state.shares.should.eql({})
                    done()
                })
            })
        })

        context("when posting reply", () => {
            it("should handle request", (done) => {
                Vue.set(target.state.contents, "1", {id: "1", text: "content", replyIds: [], shareIds: []})
                Moxios.stubRequest("/api/content/", {
                    status: 200,
                    response: {id: "6", content_type: "reply", parent: "1", text: "a cool reply"},
                })

                target.dispatch("saveReply", {
                    data: {
                        contentId: 1, text: "a cool reply",
                    },
                })

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        "1": {id: "1", text: "content", replyIds: ["6"], shareIds: []},
                    })
                    target.state.replies.should.eql({
                        "6": {
                            id: "6", content_type: "reply", parent: "1", text: "a cool reply", replyIds: [],
                            shareIds: [],
                        },
                    })
                    done()
                })
            })
        })

        context("fetching new content", () => {
            it("should handle request", (done) => {
                Vue.set(target.state, "contents", {})
                Vue.set(target.state, "unfetchedContentIds", ["6"])

                Moxios.stubRequest("/api/content/6/", {
                    status: 200,
                    response: {id: "6", text: "Yolo"},
                })

                target.dispatch("getNewContent", {params: {pk: "6"}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({"6": {id: "6", text: "Yolo"}})
                    done()
                })
            })
        })
    })

    describe("mutations", () => {
        describe("disableLoadMore", () => {
            it("should turn off hasLoadMore flag", () => {
                let state = {contents: {"1": {"id": getFakeContent({id: 1, hasLoadMore: true})}}}
                mutations.disableLoadMore(state, "1")
                state.contents["1"].hasLoadMore.should.be.false
            })
        })

        describe("receivedNewContent", () => {
            it("should insert id to 'state.unfetchedContentIds'", () => {
                let state = {unfetchedContentIds: []}
                mutations.receivedNewContent(state, "6")
                state.unfetchedContentIds.should.eql(["6"])
            })
        })

        describe("newContentAck", () => {
            it("should add all elements from 'state.unfetchedContentIds' to 'state.contentIds'", () => {
                let state = {unfetchedContentIds: ["6"], contentIds: []}
                mutations.newContentAck(state)
                state.contentIds.should.eql(["6"])
            })
            it("should not create duplicates in 'state.contentIds'", () => {
                let state = {unfetchedContentIds: ["6"], contentIds: ["6"]}
                mutations.newContentAck(state)
                state.contentIds.should.eql(["6"])
            })

            it("should remove all ids from unfetched ids content list", () => {
                let state = {unfetchedContentIds: ["6", "7", "8"], contentIds: []}
                mutations.newContentAck(state)
                state.unfetchedContentIds.should.eql([])
            })
        })

        describe("setLayoutDoneAfterTwitterOEmbeds", () => {
            it("should set the state correctly", () => {
                let state = {layoutDoneAfterTwitterOEmbeds: false}
                mutations.setLayoutDoneAfterTwitterOEmbeds(state, true)
                state.layoutDoneAfterTwitterOEmbeds.should.be.true
                mutations.setLayoutDoneAfterTwitterOEmbeds(state, false)
                state.layoutDoneAfterTwitterOEmbeds.should.be.false
            })
        })
    })

    describe("actions", () => {
        describe("disableLoadMore", () => {
            it("should commit with the correct parameters", () => {
                let commit = Sinon.spy()
                actions.disableLoadMore({commit}, 10)
                commit.getCall(0).args.should.eql(["disableLoadMore", 10])
            })
        })

        describe("receivedNewContent", () => {
            it("should commit with the correct parameters", () => {
                let commit = Sinon.spy()
                actions.receivedNewContent({commit}, 10)
                commit.getCall(0).args.should.eql(["receivedNewContent", 10])
            })
        })

        describe("newContentAck", () => {
            it("should commit with the correct parameters", () => {
                let state = {unfetchedContentIds: []}
                let commit = Sinon.spy()
                let dispatch = Sinon.spy()
                actions.newContentAck({commit, state, dispatch})
                commit.getCall(0).args[0].should.equal("newContentAck")
            })

            it("should dispatch 'streamOperations.getNewContent' for every unfetched ID", () => {
                let state = {unfetchedContentIds: [1, 2, 3]}
                let commit = Sinon.spy()
                let dispatch = Sinon.stub().returns(new Promise(resolve => resolve()))
                actions.newContentAck({commit, state, dispatch})
                dispatch.getCall(0).args.should.eql(["getNewContent", {params: {pk: 1}}])
                dispatch.getCall(1).args.should.eql(["getNewContent", {params: {pk: 2}}])
                dispatch.getCall(2).args.should.eql(["getNewContent", {params: {pk: 3}}])
            })

            it("should always resolve even if one dispatch operation fails", (done) => {
                let state = {unfetchedContentIds: [1, 2, 3]}
                let commit = Sinon.spy()
                let dispatch = Sinon.stub()
                    .onCall(0).returns(Promise.resolve())
                    .onCall(1).returns(Promise.reject("Fetch error"))
                    .onCall(2).returns(Promise.resolve())

                actions.newContentAck({commit, state, dispatch}).should.be.fulfilled.notify(done)
            })

            it("should re-add ID if one dispatch operation fails", (done) => {
                let state = {unfetchedContentIds: [1, 2, 3], contentIds: []}
                let commit = (name) => mutations[name](state)
                let dispatch = Sinon.stub()
                    .onCall(0).returns(Promise.resolve())
                    .onCall(1).returns(Promise.reject("Fetch error"))
                    .onCall(2).returns(Promise.resolve())

                actions.newContentAck({commit, state, dispatch}).then(() => {
                    state.unfetchedContentIds.should.eql([2])
                    done()
                })
            })

        })

        describe("setLayoutDoneAfterTwitterOEmbeds", () => {
            it("should commit mutation correctly", () => {
                // let state = {layoutDoneAfterTwitterOEmbeds: false}
                let commit = Sinon.spy()
                // let dispatch = Sinon.spy()
                actions.setLayoutDoneAfterTwitterOEmbeds({commit}, true)
                commit.getCall(0).args[0].should.equal("setLayoutDoneAfterTwitterOEmbeds")
                commit.getCall(0).args[1].should.be.true
            })
        })
    })

    describe("getters", () => {
        describe("contentList", () => {
            it("should only return existing posts", () => {
                let state = {
                    contentIds: ["1", "2", "3", "4", "5"],
                    contents: {
                        "1": {id: "1"},
                        "3": {id: "3"},
                        "5": {id: "5"},
                    },
                }
                getters.contentList(state).should.eql([{id: "1"}, {id: "3"}, {id: "5"}])
            })
        })

        describe("replies", () => {
            it("returns replies for correct content", () => {
                let state = {
                    contents: {
                        "1": {id: "1", replyIds: ["2", "4"]},
                        "3": {id: "3", replyIds: ["5"]},
                    },
                    replies: {
                        "2": {id: "2"},
                        "4": {id: "4"},
                        "5": {id: "5"},
                        "7": {id: "7"},
                    },
                    shares: {
                        "6": {id: "6", replyIds: ["7"]},
                    },
                }
                getters.replies(state)({id: "1", content_type: "content"}).should.eql([{id: "2"}, {id: "4"}])
                getters.replies(state)({id: "3", content_type: "content"}).should.eql([{id: "5"}])
                getters.replies(state)({id: "6", content_type: "share"}).should.eql([{id: "7"}])
            })
        })

        describe("shares", () => {
            it("returns shares for correct content", () => {
                let state = {
                    contents: {
                        "1": {id: "1", shareIds: ["2", "4"]},
                        "3": {id: "3", shareIds: ["5"]},
                    },
                    shares: {
                        "2": {id: "2"},
                        "4": {id: "4"},
                        "5": {id: "5"},
                        "7": {id: "7"},
                    },
                }
                getters.shares(state)(1).should.eql([{id: "2"}, {id: "4"}])
                getters.shares(state)(3).should.eql([{id: "5"}])
            })
        })

        describe("hasNewContent", () => {
            it("should be true if 'state.unfetchedContentIds' is not empty and content is not being fetched", () => {
                let state = newRestAPI({state: getState()}).state
                state.pending.contents = false
                state.unfetchedContentIds.push("6")

                getters.hasNewContent(state).should.be.true

                state.pending.contents = false
                state.unfetchedContentIds.length = 0

                getters.hasNewContent(state).should.be.false

                state.pending.contents = true
                state.unfetchedContentIds.push("6")

                getters.hasNewContent(state).should.be.false
            })
        })
    })
})
