<!-- eslint-disable max-len -->
<template>
    <div class="socialhome-markdown-editor" :class="{fullscreen: fullscreen}">
        <textarea v-show="false" ref="easymde" />
        <small class="form-text text-muted image-upload-form-text">
            {{ translations.publisherHelpText }}
        </small>
        <b-progress v-show="isUploading" :value="uploadedSize" show-progress animated />

        <div v-show="showDropdowns.headings" class="editor-toolbar-dropdown editor-toolbar-heading-dropdown">
            <ul>
                <li>
                    <b-button @click="toggleHeading1">
                        <h1>{{ "Header 1" | gettext }}</h1>
                    </b-button>
                </li>
                <li>
                    <b-button @click="toggleHeading2">
                        <h2>{{ "Header 2" | gettext }}</h2>
                    </b-button>
                </li>
                <li>
                    <b-button @click="toggleHeading3">
                        <h3>{{ "Header 3" | gettext }}</h3>
                    </b-button>
                </li>
                <li>
                    <b-button @click="toggleHeading4">
                        <h4>{{ "Header 4" | gettext }}</h4>
                    </b-button>
                </li>
                <li>
                    <b-button @click="toggleHeading5">
                        <h5>{{ "Header 5" | gettext }}</h5>
                    </b-button>
                </li>
                <li>
                    <b-button @click="toggleHeading6">
                        <h6>{{ "Header 6" | gettext }}</h6>
                    </b-button>
                </li>
            </ul>
        </div>
        <div
            v-show="showDropdowns.pictures"
            v-if="uploadImage"
            class="editor-toolbar-dropdown editor-toolbar-picture-dropdown"
        >
            <ul>
                <li>
                    <b-button block :title="translations.insertImage" @click.stop.prevent="embedPictureLink">
                        {{ "By url" | gettext }}
                    </b-button>
                </li>
                <li>
                    <b-button
                        block
                        :title="translations.uploadImage"
                        @click.stop.prevent="onUploadImage"
                    >
                        {{ translations.uploadImage }}
                    </b-button>
                </li>
            </ul>
        </div>

        <!-- "Hidden" form for image upload input -->
        <form v-show="false" ref="uploadform" enctype="multipart/form-data">
            <input
                ref="uploadforminput"
                type="file"
                multiple
                name="image"
                accept="image/*"
                @change.stop.prevent="() => processImages($refs.uploadforminput.files)"
            >
        </form>
    </div>
</template>
<!-- eslint-enable max-len -->

<script>
import EasyMDE from "easymde"
import Popper from "popper.js"
import Cookies from "js-cookie"
import _debounce from "lodash/debounce"
import _get from "lodash/get"

export default {
    name: "MarkdownEditor",
    props: {
        autosave: {
            type: Boolean, default: false,
        },
        uploadImage: {
            type: Boolean, default: true,
        },
        value: {
            type: String, default: "",
        },
    },
    data() {
        return {
            fullscreen: false,
            images: {
                uploading: {},
                success: {},
                error: {},
            },
            rendered: "",
            showDropdowns: {
                headings: false,
                pictures: false,
            },
        }
    },
    computed: {
        isUploading() {
            return Object.values(this.images.uploading).length > 0
        },
        translations() {
            return {
                bold: gettext("Bold"),
                fullscreen: gettext("Toggle fullscreen (F11)"),
                guide: gettext("Markdown guide"),
                "heading-dropdown": gettext("Heading"),
                "horizontal-rule": gettext("Insert Horizontal Line"),
                imageUploadFail: imageName => interpolate(gettext("The image %s couldn't be uploaded"), [imageName]),
                insertImage: gettext("add an image using an url (Ctrl-Alt-I)"),
                italic: gettext("Italic"),
                link: gettext("Create Link"),
                loading: gettext("Loading..."),
                "ordered-list": gettext("Numbered List"),
                "picture-dropdown": gettext("Insert image"),
                preview: gettext("Toggle preview (Ctrl-P)"),
                publisherHelpText: gettext("You can upload images using the camera icon or by dragging them "
                    + "to the text area. Valid file types: png/jpg/svg/gif."),
                quote: gettext("Quote"),
                "unordered-list": gettext("Generic List"),
                uploadImage: gettext("Upload image"),
                "side-by-side": gettext("Toggle side by side (F9)"),
            }
        },
        uploadedSize() {
            const [totalSize, uploadedSize] = Object.keys(this.images.uploading)
                .map(name => [
                    _get(this.images.uploading[name], ["image", "size"], 0),
                    _get(this.images.uploading[name], ["uploadedSize"], 0),
                ]).reduce((acc, curr) => [acc[0] + curr[0], acc[1] + curr[1]], [0, 0])
            return Math.round(totalSize === 0 ? 100 : Math.min((uploadedSize * 100) / totalSize, 100))
        },
    },
    mounted() {
        const debounced = _debounce((md, preview) => {
            if (md.trim().length === 0) {
                return ""
            }

            if (!this.$editor.isPreviewActive() && !this.$editor.isSideBySideActive()) {
                return ""
            }

            this.render(md, preview)
            return `<div class="alert alert-success" role="alert">${this.translations.loading}</div>${this.rendered}`
        }, 1000, {maxWait: 3000})
        // Trigger first result
        debounced("")

        this.$editor = new EasyMDE({
            autoDownloadFontAwesome: false,
            autofocus: true,
            element: this.$refs.easymde,
            autosave: {enabled: false},
            indentWithTabs: false,
            previewRender: debounced,
            promptURLs: true,
            spellChecker: false,
            toolbar: [
                "bold",
                "italic",
                /* "strikethrough",  // Disabled for now */
                {
                    name: "heading-dropdown",
                    action: this.toggleHeadingDropdown,
                    className: "fa fa-header fa-heading heading-dropdown-button",
                },
                "horizontal-rule",
                "|",
                "quote",
                "code",
                "|",
                "unordered-list",
                "ordered-list",
                /*
                 * "|",
                 * "table",  // Nope. not yet...
                 */
                "|",
                "link",
                {
                    name: "picture-dropdown",
                    action: this.pictureClickAction,
                    className: "fa fa-camera picture-dropdown-button",
                },
                {
                    name: "guide",
                    action: "https://www.markdownguide.org/basic-syntax/",
                    className: "fa fa-question-circle",
                },
                {
                    name: "fullscreen",
                    action: () => this.$editor.toggleFullScreen(),
                    className: "fa fa-arrows-alt no-disable no-mobile",
                },
                {
                    name: "side-by-side",
                    action: () => this.$editor.toggleSideBySide(),
                    className: "fa fa-columns no-disable no-mobile",
                },
                {
                    name: "preview",
                    action: () => this.$editor.togglePreview(),
                    className: "fa fa-eye no-disable",
                },
            ],
        })

        // Hack to set tooltip translations without having to explicitely
        // define all toolbar buttons attributes.
        // TODO: toolbar button translations? FontAwsome doesn't seem to be
        // localized...
        const toolbar = document.getElementsByClassName("editor-toolbar")[0]
        toolbar.remove()
        this.$editor.createToolbar(this.$editor.toolbar.map(element => {
            if (this.translations[element.name]) {
                // eslint-disable-next-line no-param-reassign
                element.title = this.translations[element.name]
            }
            return element
        }))

        // Sync with parent's v-model (see https://alligator.io/vuejs/add-v-model-support/)
        this.$editor.value(this.value)
        this.$editor.codemirror.on("change", () => this.$emit("input", this.$editor.value()))

        // Bind event to close dropdowns when clicking outside them
        this.$editor.codemirror.on("optionChange", () => { this.fullscreen = this.$editor.isFullscreenActive() })
        document.body.addEventListener("click", this.bodyClickEventListener)
        document.body.addEventListener("auxclick", this.bodyClickEventListener)

        try {
            // Create heading dropdown
            const node1 = this.$el.querySelectorAll(".heading-dropdown-button")[0]
            const popper1 = this.$el.querySelectorAll(".editor-toolbar-heading-dropdown")[0]
            this.$headingDropdown = new Popper(node1, popper1, {placement: "bottom"})

            // Create image upload dropdown
            if (this.uploadImage !== undefined) {
                const node2 = this.$el.querySelectorAll(".picture-dropdown-button")[0]
                const popper2 = this.$el.querySelectorAll(".editor-toolbar-picture-dropdown")[0]
                this.$pictureDropdown = new Popper(node2, popper2, {placement: "bottom"})
                this.$el.querySelector(".CodeMirror-wrap").addEventListener("drop", this.onImageDrop)
            }
            // eslint-disable-next-line no-empty
        } catch (_) {}
    },
    beforeDestroy() {
        document.body.removeEventListener("click", this.bodyClickEventListener)
        document.body.removeEventListener("auxclick", this.bodyClickEventListener)
        this.$el.querySelector(".CodeMirror-wrap").removeEventListener("drop", this.onImageDrop)
    },
    methods: {
        bodyClickEventListener(event) {
            if (event.target.closest(".editor-toolbar-dropdown") === null
                && event.target.closest(".editor-toolbar") === null) {
                this.hideDropdowns()
            }
        },
        embedPictureLink() {
            this.hideDropdowns()
            setTimeout(() => this.$nextTick(() => this.$editor.drawImage()), 5)
        },
        hideDropdowns() {
            Object.keys(this.showDropdowns).forEach(item => this.$set(this.showDropdowns, item, false))
        },
        insertImage(url) {
            const cursor = this.$editor.codemirror.getCursor()
            const line = this.$editor.codemirror.getLine(cursor.line)
            const prefix = line.trim().length > 0 ? "  \n" : ""
            const from = line.trim().length !== line.length ? {
                line: cursor.line, ch: 0,
            } : cursor
            const to = line.trim().length !== line.length ? cursor : undefined
            const mkdImg = `${prefix}![](${url})  \n`
            this.$editor.codemirror.replaceRange(mkdImg, from, to)
            this.$editor.codemirror.focus()
        },
        onImageDrop(event) {
            this.processImages(event.dataTransfer.files)
        },
        pictureClickAction() {
            if (this.uploadImage) {
                this.togglePictureDropdown()
            } else {
                this.$editor.drawImage()
            }
        },
        processImages(fileList) {
            for (let i = 0; i < fileList.length; i++) {
                if (fileList[i].type.startsWith("image")) {
                    this.$set(this.images.uploading, fileList[i].name, {
                        image: fileList[i], uploadedSize: 0,
                    })
                }
            }

            this.$refs.uploadform.reset()

            const promiseSuccess = (data, image) => {
                this.$set(this.images.success, image.name, image)
                this.insertImage(data.url)
                return data.url
            }

            const promiseFail = image => {
                this.$set(this.images.error, image.name, image)
                this.$snotify.error(this.translations.imageUploadFail(image.name))
                    .on("destroyed", () => this.$delete(this.images.error, image.name))
            }

            return Object.values(this.images.uploading).map(filePointer => {
                const {image} = filePointer
                const formData = new FormData()
                formData.append("image", image, image.name)

                return this.$http.post(Urls["api-image-upload"](), formData, {
                    headers: {
                        ...this.$http.headers, "content-type": "multipart/form-data",
                    },
                    onUploadProgress: e => this.$set(this.images.uploading[image.name], "uploadedSize", e.loaded),
                }).then(({data}) => promiseSuccess(data, image), () => promiseFail(image)).finally(() => {
                    this.$delete(this.images.uploading, image.name)
                })
            })
        },
        render(plainText, preview) {
            const formData = new FormData()
            formData.append("content", plainText)
            formData.append("csrfmiddlewaretoken", Cookies.get("csrftoken"))

            this.$http
                .post(Urls.markdownx_markdownify(), formData, {headers: {"content-type": "multipart/form-data"}})
                // eslint-disable-next-line no-multi-assign,no-param-reassign
                .then(({data}) => { this.rendered = preview.innerHTML = data })
                // eslint-disable-next-line no-param-reassign
                .catch(() => { preview.innerHTML = this.rendered })
        },
        toggleHeadingDropdown() {
            const newValue = !this.showDropdowns.headings
            this.hideDropdowns()
            this.showDropdowns.headings = newValue
            if (this.showDropdowns.headings) {
                this.$nextTick(this.$headingDropdown.update)
            }
        },
        toggleHeading1() {
            this.$editor.toggleHeading1()
            this.hideDropdowns()
        },
        toggleHeading2() {
            this.$editor.toggleHeading2()
            this.hideDropdowns()
        },
        toggleHeading3() {
            this.$editor.toggleHeading3()
            this.hideDropdowns()
        },
        toggleHeading4() {
            this.$editor.toggleHeading3()
            this.$editor.toggleHeadingSmaller()
            this.hideDropdowns()
        },
        toggleHeading5() {
            this.$editor.toggleHeading3()
            this.$editor.toggleHeadingSmaller()
            this.$editor.toggleHeadingSmaller()
            this.hideDropdowns()
        },
        toggleHeading6() {
            this.$editor.toggleHeading3()
            this.$editor.toggleHeadingSmaller()
            this.$editor.toggleHeadingSmaller()
            this.$editor.toggleHeadingSmaller()
            this.hideDropdowns()
        },
        togglePictureDropdown() {
            const newValue = !this.showDropdowns.pictures
            this.hideDropdowns()
            this.showDropdowns.pictures = newValue
            if (this.showDropdowns.pictures) {
                this.$nextTick(this.$pictureDropdown.update)
            }
        },
        onUploadImage() {
            this.$refs.uploadforminput.click()
            this.hideDropdowns()
        },
    },
}
</script>

<style lang="scss">
  .socialhome-markdown-editor {
    &.fullscreen > * {
      margin-top: 45px;
    }

    .image-upload-form-text {
      margin: 0;
      padding-bottom: 8px;
    }

    .progress {
      margin-bottom: 8px;
      padding: 0;
    }

    .editor-toolbar {
      background-color: white;
    }

    .editor-statusbar {
      margin: 0;
      padding-bottom: 0;
    }

    .editor-toolbar-dropdown {
      background-color: white;
      border: 1px solid black;
      color: #000;
      z-index: 1030;

      ul {
        list-style-type: none;

        .btn {
          border: none;
        }
      }
    }

    .editor-toolbar-heading-dropdown ul {
      align-items: center;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-around;
      margin: 0;
      padding: 8px;
      width: 385px;

      .btn {
        margin: 2px;
      }
    }

    .editor-toolbar-picture-dropdown ul {
      padding: 0;
      margin: 0;
    }

    .editor-preview {
        color: #000;
    }
  }
</style>
