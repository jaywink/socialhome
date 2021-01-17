import Vue from "vue"
import {mount} from "avoriaz"

import MarkdownEditor from "@/components/publisher/MarkdownEditor"

describe("MarkdownEditor", () => {
    beforeEach(() => {
        Sinon.restore()
    })

    describe("isUploading", () => {
        it("should display the progress bar when an image is uploading", () => {
            const target = mount(MarkdownEditor)

            target.instance().isUploading.should.eq(false)
            Vue.set(target.instance().images.uploading, "9fcd33e0-b2c0-4548-b59d-3a79651209d4", {
                image: {size: 5699},
                uploadedSize: 0,
            })
            target.instance().isUploading.should.eq(true)
        })
    })

    describe("uploadedSize", () => {
        it("should be 100 when no images are being uploaded", () => {
            const target = mount(MarkdownEditor)

            target.instance().uploadedSize.should.eq(100)
        })

        it("should compute the correct uploading size", () => {
            const target = mount(MarkdownEditor)
            Vue.set(target.instance().images.uploading, "9fcd33e0-b2c0-4548-b59d-3a79651209d4", {
                image: {size: 5699},
                uploadedSize: 0,
            })
            Vue.set(target.instance().images.uploading, "f3bdeb4b-1a04-43c3-89b6-78e2c2c24a2e", {
                image: {size: 88654},
                uploadedSize: 8865,
            })
            Vue.set(target.instance().images.uploading, "01e25466-0a55-4f7d-951d-aefec9a22d4b", {
                image: {size: 88659},
                uploadedSize: 44775,
            })

            target.instance().uploadedSize.should.eq(29)
        })
    })

    describe("processImages", () => {
        const images = [
            new File(new Array(88659).fill(0b0),
                "01e25466-0a55-4f7d-951d-aefec9a22d4b", {type: "image/jpg"}),
            new File(new Array(88654).fill(0b0),
                "f3bdeb4b-1a04-43c3-89b6-78e2c2c24a2e", {type: "image/jpg"}),
            new File(new Array(5699).fill(0b0),
                "9fcd33e0-b2c0-4548-b59d-3a79651209d4", {type: "image/jpg"}),
        ]
        const result = {data: {url: "http://localhost/01e25466-0a55-4f7d-951d-aefec9a22d4b"}}

        beforeEach(() => {
            Sinon.stub(Vue.prototype.$http, "post").returns(Promise.resolve(result))
        })

        afterEach(() => {
            Vue.prototype.$http.post.reset()
        })

        it("should correctly set images data", () => {
            const target = mount(MarkdownEditor)
            target.instance().processImages(images)
            target.instance().images.uploading.should.eql({
                "01e25466-0a55-4f7d-951d-aefec9a22d4b": {
                    image: images[0],
                    uploadedSize: 0,
                },
                "f3bdeb4b-1a04-43c3-89b6-78e2c2c24a2e": {
                    image: images[1],
                    uploadedSize: 0,
                },
                "9fcd33e0-b2c0-4548-b59d-3a79651209d4": {
                    image: images[2],
                    uploadedSize: 0,
                },
            })
        })

        it("should post the images", () => {
            const target = mount(MarkdownEditor)
            target.instance().processImages(images)
            target.instance().$http.post.should.have.been.calledWithExactly(
                "/api/image-upload/",
                Sinon.match.instanceOf(FormData),
                Sinon.match({
                    headers: Sinon.match.hasOwn("content-type", "multipart/form-data"),
                    onUploadProgress: Sinon.match.func,
                }),
            )
        })

        it("should remove the images from uploadings when HTTP request has succeded of failed", done => {
            Vue.prototype.$http.post
                .onFirstCall().returns(Promise.resolve(result))
                .onSecondCall().returns(Promise.reject(new DOMException()))
                .onThirdCall()
                .returns(Promise.reject(new DOMException()))

            const target = mount(MarkdownEditor).instance()
            Sinon.spy(target, "$delete")
            Promise.all(target.processImages(images)).finally(() => {
                target.$delete.should.have.been.calledThrice
                target.$delete.firstCall.should.have.been
                    .calledWithExactly(target.images.uploading, "01e25466-0a55-4f7d-951d-aefec9a22d4b")
                target.$delete.secondCall.should.have.been
                    .calledWithExactly(target.images.uploading, "f3bdeb4b-1a04-43c3-89b6-78e2c2c24a2e")
                target.$delete.thirdCall.should.have.been
                    .calledWithExactly(target.images.uploading, "9fcd33e0-b2c0-4548-b59d-3a79651209d4")
                done()
            }).catch(done)
        })

        it("should update image progress", () => {
            // eslint-disable-next-line no-unused-vars
            Vue.prototype.$http.post.returns(new Promise((res, rej) => {}))

            const target = mount(MarkdownEditor).instance()
            target.processImages(images)
            target.images.uploading.should.eql({
                "01e25466-0a55-4f7d-951d-aefec9a22d4b": {
                    image: images[0],
                    uploadedSize: 0,
                },
                "f3bdeb4b-1a04-43c3-89b6-78e2c2c24a2e": {
                    image: images[1],
                    uploadedSize: 0,
                },
                "9fcd33e0-b2c0-4548-b59d-3a79651209d4": {
                    image: images[2],
                    uploadedSize: 0,
                },
            })
            target.$http.post.firstCall.args[2].onUploadProgress({loaded: 23})
            target.images.uploading.should.eql({
                "01e25466-0a55-4f7d-951d-aefec9a22d4b": {
                    image: images[0],
                    uploadedSize: 23,
                },
                "f3bdeb4b-1a04-43c3-89b6-78e2c2c24a2e": {
                    image: images[1],
                    uploadedSize: 0,
                },
                "9fcd33e0-b2c0-4548-b59d-3a79651209d4": {
                    image: images[2],
                    uploadedSize: 0,
                },
            })
        })
    })
})
