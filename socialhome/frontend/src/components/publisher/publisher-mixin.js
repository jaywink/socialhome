import _isString from "lodash/isString"
import _isObject from "lodash/isObject"
import _get from "lodash/get"

import MarkdownEditor from "@/components/publisher/MarkdownEditor"
import SimpleLoadingElement from "@/components/common/SimpleLoadingElement"

const VISIBILITY_OPTIONS = Object.freeze({
    PUBLIC: {
        value: 0,
        text: gettext("Public"),
        help: gettext("visible to anyone, even anonymous users and internet search bots."),
    },
    LIMITED: {
        value: 1,
        text: gettext("Limited"),
        help: gettext("visible only to those mentioned in the text and/or your mutuals."),
    },
    SITE: {
        value: 2,
        text: gettext("Site"),
        help: gettext("visible to only users who are logged in. Does not federate to other servers."),
    },
    SELF: {
        value: 3,
        text: gettext("Self"),
        help: gettext("visible to only self. Does not federate to other servers."),
    },
})

const publisherMixin = {
    components: {
        MarkdownEditor, SimpleLoadingElement,
    },
    data() {
        return {
            baseModel: {
                showPreview: true,
                text: _get(window, ["context", "mentions"], ""),
            },
            extendedModel: {},
            errors: {
                recipientsErrors: "",
                includeFollowingErrors: "",
                recipientsNotFoundErrors: [],
            },
            wasValidated: null,
            isPosting: false,
            renderedText: _get(window, ["context", "rendered"], ""),
        }
    },
    computed: {
        model() {
            return {
                ...this.baseModel,
                ...this.extendedModel,
            }
        },
        titleText() {
            throw new Error("`titleText` must be overriden")
        },
        translations() {
            return {
                create: gettext("Create"),
                edit: gettext("Edit"),
                federate: gettext("Federate to remote servers"),
                federateHelp: gettext("Disable to skip federating this version to remote servers. "
                    + "Note, saved content version will still be updated to local streams."),
                hiddenTextarea: gettext("Hidden textarea"),
                includeFollowing: gettext("Include your mutuals"),
                includeFollowingHelp: gettext("Automatically include people you follow "
                    + "that also follow you as recipients."),
                recipients: `${gettext("Recipients")}:`,
                recipientsHelp: gettext("Enter the recipients' handles (eg @user@example.com) "
                    + "in the editor window. Sorry, no search yet... "),
                reply: gettext("Reply"),
                updateReply: gettext("Update reply"),
                visibility: gettext("Visibility"),
                visibilityHelp: gettext("Tip: You can use the \"Self\" visibility to create draft content and then"
                    + " change the visibility to for example \"Public\" when you want to publish it."),
                pinned: gettext("Pinned to profile"),
                pinnedHelp: gettext("Pinned content will be shown on your personal profile "
                    + "in the order you want. Reorder pinned content from the profile menu. "
                    + "Pinned content will federate and otherwise function as any other content."),
                postUploadError: gettext("Error saving content."),
                showPreview: gettext("Show OEmbed or OpenGraph preview"),
                showPreviewHelp: gettext("Disable to turn off fetching and showing an OEmbed or "
                    + "OpenGraph preview using the links in the text."),
                limitedVisibilityError: gettext("When visibility is set to 'Limited', you must either "
                    + "mention recipients in the text or include your mutuals."),
                recipientsNotFoundError: gettext("Some recipients couldn't be found."),
                validationError: gettext("Validation error"),
            }
        },
        visibilityOptions() {
            return VISIBILITY_OPTIONS
        },
    },
    methods: {
        // eslint-disable-next-line no-unused-vars
        handleRequestErrors(code, message, payload = {}) {
            this.$snotify.error(message, {timeout: 10000})
        },
        postFormRequest() {
            throw new Error("`postFormRequest` must be overriden")
        },
        // TODO: implement search UI
        extractMentions() {
            const cm = this.$refs.editor.$editor.codemirror
            const cur = cm.getSearchCursor(/@([\w\-.]+@[\w\-.]+\.[A-Za-z0-9]+)[\W\s]?/)
            let match = cur.findNext()
            this.extendedModel.recipients = []
            while (match) {
                this.extendedModel.recipients.push(match[1])
                match = cur.findNext()
            }
        },
        async onPostForm() {
            if (this.isPosting === true) return

            this.isPosting = true
            try {
                const url = await this.postFormRequest()
                window.location.replace(url)
            } catch (error) {
                this.isPosting = false

                const data = _get(error, ["response", "data"])
                let {message} = error

                if (_isObject(data)) {
                    const errObject = _get(Object.values(data), "[0]")
                    const {code, payload} = errObject

                    if (_isString(code)) {
                        message = errObject.message
                        this.handleRequestErrors(code, message, payload)
                        return
                    }
                }

                if (_isString(message)) {
                    this.$snotify.error(message, {timeout: 10000})
                    return
                }

                this.$snotify.error(this.translations.postUploadError, {timeout: 10000})
            }
        },
    },
}

export {publisherMixin, VISIBILITY_OPTIONS}
export default publisherMixin
