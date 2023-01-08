import Moxios from "moxios"
import Vue from "vue"
import Vuex from "vuex"
import Axios from "axios"
import uuid from "uuid"

import getState from "@/store/modules/stream.state"
import {
    actions,
    addHasLoadMore,
    fetchContentsSuccess,
    fetchNewContentSuccess,
    fetchRepliesSuccess,
    fetchSharesSuccess,
    getters,
    mutations,
    newRestAPI,
    onError,
} from "@/store/modules/stream"
import {getFakeContent} from "%fixtures/jsonContext.fixtures"

Vue.use(Vuex)

const UUID = uuid()

describe("streamStore", () => {
    afterEach(() => {
        Sinon.restore()
    })

    describe("addHasLoadMore", () => {
        it("adds flag on fifth last content", () => {
            const state = {
                currentContentIds: [...new Array(7).keys()].map(i => i), contents: {},
            }
            state.currentContentIds.forEach(id => {
                state.contents[id] = getFakeContent({
                    id, hasLoadMore: false,
                })
            })
            addHasLoadMore(state)
            state.contents[state.currentContentIds[0]].hasLoadMore.should.be.false
            state.contents[state.currentContentIds[1]].hasLoadMore.should.be.true
            state.contents[state.currentContentIds[2]].hasLoadMore.should.be.false
            state.contents[state.currentContentIds[3]].hasLoadMore.should.be.false
            state.contents[state.currentContentIds[4]].hasLoadMore.should.be.false
            state.contents[state.currentContentIds[5]].hasLoadMore.should.be.false
            state.contents[state.currentContentIds[6]].hasLoadMore.should.be.false
        })

        it("adds flag to last if under 5 contents", () => {
            const state = {
                currentContentIds: [...new Array(4).keys()].map(i => i), contents: {},
            }
            state.currentContentIds.forEach(id => {
                state.contents[id] = getFakeContent({
                    id, hasLoadMore: false,
                })
            })
            addHasLoadMore(state)
            state.contents[state.currentContentIds[0]].hasLoadMore.should.be.false
            state.contents[state.currentContentIds[1]].hasLoadMore.should.be.false
            state.contents[state.currentContentIds[2]].hasLoadMore.should.be.false
            state.contents[state.currentContentIds[3]].hasLoadMore.should.be.true
        })

        it("sets layoutDoneAfterTwitterOEmbeds to false", () => {
            const state = {
                currentContentIds: [...new Array(7).keys()].map(i => i),
                contents: {},
                layoutDoneAfterTwitterOEmbeds: true,
            }
            state.currentContentIds.forEach(id => {
                state.contents[id] = getFakeContent({
                    id, hasLoadMore: false,
                })
            })
            addHasLoadMore(state)
            state.layoutDoneAfterTwitterOEmbeds.should.be.false
        })
    })

    describe("fetchContentsSuccess", () => {
        it("should append payload to state", () => {
            const payload = {
                data: [
                    {
                        id: "6", text: "foobar", content_type: "content",
                    },
                    {
                        id: "7", text: "blablabla", content_type: "content",
                    },
                ],
            }

            const state = {
                allContentIds: ["1", "2"],
                currentContentIds: ["1", "2"],
                contents: {
                    1: {
                        id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: [],
                    },
                    2: {
                        id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: [],
                    },
                },
            }

            fetchContentsSuccess(state, payload)

            state.should.eql({
                allContentIds: ["1", "2", "6", "7"],
                currentContentIds: ["1", "2", "6", "7"],
                contents: {
                    1: {
                        id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: [],
                    },
                    2: {
                        id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: [],
                    },
                    6: {
                        id: "6", text: "foobar", content_type: "content", replyIds: [], shareIds: [],
                    },
                    7: {
                        id: "7",
                        text: "blablabla",
                        content_type: "content",
                        replyIds: [],
                        shareIds: [],
                        hasLoadMore: true,
                    },
                },
                layoutDoneAfterTwitterOEmbeds: false,
            })
        })
    })

    describe("fetchRepliesSuccess", () => {
        it("should append array payload to state", () => {
            const payload = {
                data: [
                    {
                        id: "6", text: "foobar", content_type: "reply", parent: "1", root_parent: "1",
                    },
                    {
                        id: "7", text: "blablabla", content_type: "reply", parent: "3", root_parent: "3",
                    },
                ],
            }

            const state = {
                allContentIds: ["1", "2", "3"],
                contents: {
                    1: {
                        id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: ["3"],
                    },
                    2: {
                        id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: [],
                    },
                    3: {
                        id: "3", content_type: "share", share_of: "1", replyIds: [],
                    },
                },
            }

            fetchRepliesSuccess(state, payload)

            state.should.eql({
                allContentIds: ["1", "2", "3", "6", "7"],
                contents: {
                    1: {
                        id: "1",
                        text: "Plop",
                        content_type: "content",
                        replyIds: ["6"],
                        reply_count: 1,
                        shareIds: ["3"],
                    },
                    2: {
                        id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: [],
                    },
                    3: {
                        id: "3", content_type: "share", share_of: "1", replyIds: ["7"],
                    },
                    6: {
                        id: "6",
                        text: "foobar",
                        content_type: "reply",
                        parent: "1",
                        root_parent: "1",
                        replyIds: [],
                        shareIds: [],
                    },
                    7: {
                        id: "7",
                        text: "blablabla",
                        content_type: "reply",
                        parent: "3",
                        root_parent: "3",
                        replyIds: [],
                        shareIds: [],
                    },
                },
            })
        })

        it("should append single item payload to state", () => {
            const payload = {
                data: {
                    id: "6", text: "foobar", content_type: "reply", root_parent: "1", parent: "1",
                },
            }

            const state = {
                allContentIds: ["1", "2", "3"],
                contents: {
                    1: {
                        id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: ["3"],
                    },
                    2: {
                        id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: [],
                    },
                    3: {
                        id: "3", content_type: "share", share_of: "1", replyIds: [],
                    },
                },
            }

            fetchRepliesSuccess(state, payload)

            state.should.eql({
                allContentIds: ["1", "2", "3", "6"],
                contents: {
                    1: {
                        id: "1",
                        text: "Plop",
                        content_type: "content",
                        replyIds: ["6"],
                        reply_count: 1,
                        shareIds: ["3"],
                    },
                    2: {
                        id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: [],
                    },
                    3: {
                        id: "3", content_type: "share", share_of: "1", replyIds: [],
                    },
                    6: {
                        id: "6",
                        text: "foobar",
                        content_type: "reply",
                        parent: "1",
                        root_parent: "1",
                        replyIds: [],
                        shareIds: [],
                    },
                },
            })
        })
    })

    describe("fetchSharesSuccess", () => {
        it("should append payload to state", () => {
            const payload = {
                data: [
                    {
                        id: "6", content_type: "share", share_of: "1",
                    },
                    {
                        id: "7", content_type: "share", share_of: "2",
                    },
                ],
            }

            const state = {
                allContentIds: ["1", "2"],
                contents: {
                    1: {
                        id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: [],
                    },
                    2: {
                        id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: [],
                    },
                },
            }

            fetchSharesSuccess(state, payload)

            state.should.eql({
                allContentIds: ["1", "2", "6", "7"],
                contents: {
                    1: {
                        id: "1", text: "Plop", content_type: "content", replyIds: [], shareIds: ["6"],
                    },
                    2: {
                        id: "2", text: "Hello!", content_type: "content", replyIds: [], shareIds: ["7"],
                    },
                    6: {
                        id: "6", content_type: "share", share_of: "1", replyIds: [],
                    },
                    7: {
                        id: "7", content_type: "share", share_of: "2", replyIds: [],
                    },
                },
            })
        })
    })

    describe("fetchNewContentSuccess", () => {
        it("should append fetched content to contents", () => {
            const payload = {
                data: {
                    id: "6", text: "Yolo",
                },
            }

            const state = {
                allContentIds: ["1", "2"],
                contents: {
                    1: {
                        id: "1", text: "Plop",
                    },
                    2: {
                        id: "2", text: "Hello!",
                    },
                },
                unfetchedContentIds: ["6"],
            }

            fetchNewContentSuccess(state, payload)

            state.allContentIds.should.eql(["1", "2", "6"])
            state.contents.should.eql({
                1: {
                    id: "1", text: "Plop",
                },
                2: {
                    id: "2", text: "Hello!",
                },
                6: {
                    id: "6", text: "Yolo",
                },
            })
        })
    })

    describe("onError", () => {
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
                    {
                        id: "6", text: "foobar",
                    },
                    {
                        id: "7", text: "blablabla",
                    },
                ],
            }
            target = new Vuex.Store(newRestAPI({
                state, baseURL: "", axios: Axios,
            }))
        })

        afterEach(() => {
            Moxios.uninstall()
        })

        context("when requesting public stream", () => {
            beforeEach(() => {
                state.stream = {name: "public"}
            })

            it("should handle public stream request", done => {
                Moxios.stubRequest("/api/streams/public/", response)

                target.dispatch("getPublicStream", {params: {}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        6: {
                            id: "6", text: "foobar", replyIds: [], shareIds: [],
                        },
                        7: {
                            id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true,
                        },
                    })
                    done()
                })
            })

            it("should handle public stream request with lastId", done => {
                Moxios.stubRequest("/api/streams/public/?last_id=8", response)

                target.dispatch("getPublicStream", {params: {lastId: 8}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        6: {
                            id: "6", text: "foobar", replyIds: [], shareIds: [],
                        },
                        7: {
                            id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true,
                        },
                    })
                    done()
                })
            })

            it("should handle public stream request error", done => {
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

            it("should handle followed stream request", done => {
                Moxios.stubRequest("/api/streams/followed/", response)

                target.dispatch("getFollowedStream", {params: {}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        6: {
                            id: "6", text: "foobar", replyIds: [], shareIds: [],
                        },
                        7: {
                            id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true,
                        },
                    })
                    done()
                })
            })

            it("should handle followed stream request with lastId", done => {
                Moxios.stubRequest("/api/streams/followed/?last_id=8", response)

                target.dispatch("getFollowedStream", {params: {lastId: 8}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        6: {
                            id: "6", text: "foobar", replyIds: [], shareIds: [],
                        },
                        7: {
                            id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true,
                        },
                    })
                    done()
                })
            })

            it("should handle followed stream request error", done => {
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
                state.stream = {
                    name: "tag", id: "yolo",
                }
            })

            it("should handle tag stream request", done => {
                Moxios.stubRequest("/api/streams/tag/yolo/", response)

                target.dispatch("getTagStream", {params: {name: "yolo"}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        6: {
                            id: "6", text: "foobar", replyIds: [], shareIds: [],
                        },
                        7: {
                            id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true,
                        },
                    })
                    done()
                })
            })

            it("should handle tag stream request with lastId", done => {
                Moxios.stubRequest("/api/streams/tag/yolo/?last_id=8", response)

                target.dispatch("getTagStream", {
                    params: {
                        name: "yolo", lastId: 8,
                    },
                })

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        6: {
                            id: "6", text: "foobar", replyIds: [], shareIds: [],
                        },
                        7: {
                            id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true,
                        },
                    })
                    done()
                })
            })

            it("should handle tag stream request error", done => {
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

            it("should handle profile stream request", done => {
                Moxios.stubRequest(`/api/streams/profile-all/${UUID}/`, response)

                target.dispatch("getProfileAll", {params: {uuid: UUID}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        6: {
                            id: "6", text: "foobar", replyIds: [], shareIds: [],
                        },
                        7: {
                            id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true,
                        },
                    })
                    done()
                })
            })

            it("should handle profile all stream request with lastId", done => {
                Moxios.stubRequest(`/api/streams/profile-all/${UUID}/?last_id=8`, response)

                target.dispatch("getProfileAll", {
                    params: {
                        uuid: UUID, lastId: 8,
                    },
                })

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        6: {
                            id: "6", text: "foobar", replyIds: [], shareIds: [],
                        },
                        7: {
                            id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true,
                        },
                    })
                    done()
                })
            })

            it("should handle profile stream request error", done => {
                Moxios.stubRequest(`/api/streams/profile-all/${UUID}/`, {status: 500})

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

            it("should handle profile stream request", done => {
                Moxios.stubRequest(`/api/streams/profile-pinned/${UUID}/`, response)

                target.dispatch("getProfilePinned", {params: {uuid: UUID}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        6: {
                            id: "6", text: "foobar", replyIds: [], shareIds: [],
                        },
                        7: {
                            id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true,
                        },
                    })
                    done()
                })
            })

            it("should handle profile pinned stream request with lastId", done => {
                Moxios.stubRequest(`/api/streams/profile-pinned/${UUID}/?last_id=8`, response)

                target.dispatch("getProfilePinned", {
                    params: {
                        uuid: UUID, lastId: 8,
                    },
                })

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        6: {
                            id: "6", text: "foobar", replyIds: [], shareIds: [],
                        },
                        7: {
                            id: "7", text: "blablabla", replyIds: [], shareIds: [], hasLoadMore: true,
                        },
                    })
                    done()
                })
            })

            it("should handle profile stream request error", done => {
                Moxios.stubRequest(`/api/streams/profile-pinned/${UUID}/`, {status: 500})

                target.dispatch("getProfilePinned", {params: {uuid: UUID}})

                Moxios.wait(() => {
                    target.state.error.contents.should.exist
                    target.state.contents.should.eql({})
                    done()
                })
            })
        })

        context("when requesting replies", () => {
            it("should handle request", done => {
                Vue.set(target.state.contents, "1", {
                    id: "1", text: "content", replyIds: [], shareIds: [],
                })
                Moxios.stubRequest("/api/content/1/replies/", {
                    status: 200,
                    response: [
                        {
                            id: "6", text: "foobar", content_type: "reply", root_parent: "1", parent: "1",
                        },
                        {
                            id: "7", text: "blablabla", content_type: "reply", root_parent: "1", parent: "1",
                        },
                    ],
                })

                target.dispatch("getReplies", {params: {id: 1}})

                Moxios.wait(() => {
                    target.state.contents.should
                        .eql({
                            1: {
                                id: "1", text: "content", replyIds: ["6", "7"], reply_count: 2, shareIds: [],
                            },
                            6: {
                                id: "6",
                                text: "foobar",
                                content_type: "reply",
                                parent: "1",
                                root_parent: "1",
                                replyIds: [],
                                shareIds: [],
                            },
                            7: {
                                id: "7",
                                text: "blablabla",
                                content_type: "reply",
                                parent: "1",
                                root_parent: "1",
                                replyIds: [],
                                shareIds: [],
                            },
                        })
                    done()
                })
            })
        })

        context("when requesting shares", () => {
            it("should handle request", done => {
                Vue.set(target.state.contents, "1", {
                    id: "1", text: "content", replyIds: [], shareIds: [],
                })
                Moxios.stubRequest("/api/content/1/shares/", {
                    status: 200,
                    response: [
                        {
                            id: "6", content_type: "share", share_of: "1",
                        },
                        {
                            id: "7", content_type: "share", share_of: "1",
                        },
                    ],
                })

                target.dispatch("getShares", {params: {id: 1}})

                Moxios.wait(() => {
                    target.state.contents.should
                        .eql({
                            1: {
                                id: "1", text: "content", replyIds: [], shareIds: ["6", "7"],
                            },
                            6: {
                                id: "6", content_type: "share", share_of: "1", replyIds: [],
                            },
                            7: {
                                id: "7", content_type: "share", share_of: "1", replyIds: [],
                            },
                        })
                    done()
                })
            })
        })

        context("when posting reply", () => {
            it("should handle request", done => {
                Vue.set(target.state.contents, "1", {
                    id: "1", text: "content", replyIds: [], shareIds: [],
                })
                Moxios.stubRequest("/api/content/", {
                    status: 200,
                    response: {
                        id: "6", content_type: "reply", root_parent: "1", parent: "1", text: "a cool reply",
                    },
                })

                target.dispatch("saveReply", {
                    data: {
                        contentId: 1, text: "a cool reply",
                    },
                })

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        1: {
                            id: "1", text: "content", replyIds: ["6"], reply_count: 1, shareIds: [],
                        },
                        6: {
                            id: "6",
                            content_type: "reply",
                            parent: "1",
                            root_parent: "1",
                            text: "a cool reply",
                            replyIds: [],
                            shareIds: [],
                        },
                    })
                    done()
                })
            })
        })

        context("fetching new content", () => {
            it("should handle request", done => {
                Vue.set(target.state, "contents", {})
                Vue.set(target.state, "unfetchedContentIds", ["6"])

                Moxios.stubRequest("/api/content/6/", {
                    status: 200,
                    response: {
                        id: "6", text: "Yolo",
                    },
                })

                target.dispatch("getNewContent", {params: {pk: "6"}})

                Moxios.wait(() => {
                    target.state.contents.should.eql({
                        6: {
                            id: "6", text: "Yolo",
                        },
                    })
                    done()
                })
            })
        })
    })

    describe("mutations", () => {
        describe("disableLoadMore", () => {
            it("should turn off hasLoadMore flag", () => {
                const state = {
                    contents: {
                        1: {
                            id: getFakeContent({
                                id: 1, hasLoadMore: true,
                            }),
                        },
                    },
                }
                mutations.disableLoadMore(state, "1")
                state.contents["1"].hasLoadMore.should.be.false
            })
        })

        describe("receivedNewContent", () => {
            it("should insert id to 'state.unfetchedContentIds'", () => {
                const state = {unfetchedContentIds: []}
                mutations.receivedNewContent(state, {
                    contentId: "6", parentId: null,
                })
                state.unfetchedContentIds.should.eql(["6"])
            })
        })

        describe("newContentAck", () => {
            it("should add all elements from 'state.unfetchedContentIds' to 'state.currentContentIds'", () => {
                const state = {
                    unfetchedContentIds: ["6"], currentContentIds: [],
                }
                mutations.newContentAck(state)
                state.currentContentIds.should.eql(["6"])
            })
            it("should not create duplicates in 'state.currentContentIds'", () => {
                const state = {
                    unfetchedContentIds: ["6"], currentContentIds: ["6"],
                }
                mutations.newContentAck(state)
                state.currentContentIds.should.eql(["6"])
            })

            it("should remove all ids from unfetched ids content list", () => {
                const state = {
                    unfetchedContentIds: ["6", "7", "8"], currentContentIds: [],
                }
                mutations.newContentAck(state)
                state.unfetchedContentIds.should.eql([])
            })
        })

        describe("setLayoutDoneAfterTwitterOEmbeds", () => {
            it("should set the state correctly", () => {
                const state = {layoutDoneAfterTwitterOEmbeds: false}
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
                const commit = Sinon.spy()
                actions.disableLoadMore({commit}, 10)
                commit.getCall(0).args.should.eql(["disableLoadMore", 10])
            })
        })

        describe("receivedNewContent", () => {
            it("should commit with the correct parameters", () => {
                const commit = Sinon.spy()
                actions.receivedNewContent({commit}, 10)
                commit.getCall(0).args.should.eql(["receivedNewContent", 10])
            })
        })

        describe("newContentAck", () => {
            it("should commit with the correct parameters", () => {
                const state = {
                    unfetchedContentIds: [],
                    stream: {name: "foobar"},
                }
                const commit = Sinon.spy()
                const dispatch = Sinon.spy()
                actions.newContentAck({
                    commit, state, dispatch,
                })
                commit.getCall(0).args[0].should.equal("newContentAck")
            })

            it("should dispatch 'streamOperations.getNewContent' for every unfetched ID", () => {
                const state = {
                    unfetchedContentIds: [1, 2, 3],
                    stream: {name: "foobar"},
                }
                const commit = Sinon.spy()
                const dispatch = Sinon.stub()
                actions.newContentAck({
                    commit, state, dispatch,
                })
                dispatch.getCall(0).args.should.eql(["getFoobarStream", {params: {acceptIds: [1, 2, 3]}}])
            })
        })

        describe("setLayoutDoneAfterTwitterOEmbeds", () => {
            it("should commit mutation correctly", () => {
                // let state = {layoutDoneAfterTwitterOEmbeds: false}
                const commit = Sinon.spy()
                // let dispatch = Sinon.spy()
                actions.setLayoutDoneAfterTwitterOEmbeds({commit}, true)
                commit.getCall(0).args[0].should.equal("setLayoutDoneAfterTwitterOEmbeds")
                commit.getCall(0).args[1].should.be.true
            })
        })
    })

    describe("getters", () => {
        describe("currentContentList", () => {
            it("should only return existing posts", () => {
                const state = {
                    currentContentIds: ["1", "2", "3", "4", "5"],
                    contents: {
                        1: {id: "1"},
                        3: {id: "3"},
                        5: {id: "5"},
                    },
                }
                getters.currentContentList(state).should.eql([{id: "1"}, {id: "3"}, {id: "5"}])
            })
        })

        describe("replies", () => {
            it("returns replies for correct content", () => {
                const state = {
                    contents: {
                        1: {
                            id: "1", replyIds: ["2", "4"],
                        },
                        3: {
                            id: "3", replyIds: ["5"],
                        },
                        2: {id: "2"},
                        4: {id: "4"},
                        5: {id: "5"},
                        7: {id: "7"},
                        6: {
                            id: "6", replyIds: ["7"],
                        },
                    },
                }
                getters.replies(state)({
                    id: "1", content_type: "content",
                }).should.eql([{id: "2"}, {id: "4"}])
                getters.replies(state)({
                    id: "3", content_type: "content",
                }).should.eql([{id: "5"}])
                getters.replies(state)({
                    id: "6", content_type: "share",
                }).should.eql([{id: "7"}])
            })
        })

        describe("shares", () => {
            it("returns shares for correct content", () => {
                const state = {
                    contents: {
                        1: {
                            id: "1", shareIds: ["2", "4"],
                        },
                        3: {
                            id: "3", shareIds: ["5"],
                        },
                        2: {id: "2"},
                        4: {id: "4"},
                        5: {id: "5"},
                        7: {id: "7"},
                    },
                }
                getters.shares(state)(1).should.eql([{id: "2"}, {id: "4"}])
                getters.shares(state)(3).should.eql([{id: "5"}])
            })
        })

        describe("hasNewContent", () => {
            it("should be true if 'state.unfetchedContentIds' is not empty and content is not being fetched", () => {
                const {state} = newRestAPI({state: getState()})
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
