import MarkdownEditor from "@/components/publisher/MarkdownEditor"


const VISIBILITY_OPTIONS = Object.freeze({
    PUBLIC: {
        value: 0,
        text: gettext("Public"),
        help: gettext("visible to anyone, even anonymous users and internet search bots."),
    },
    LIMITED: {
        value: 1,
        text: gettext("Limited"),
        help: gettext("visible to only those who shared with."),
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
    components: {MarkdownEditor},
    data() {
        return {
            baseModel: {
                showPreview: true,
                text: "",
            },
            extendedModel: {},
            errors: {recipientsErrors: ""},
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
                includeFollowing: gettext("Include people I follow"),
                recipients: gettext("Recipients"),
                recipientsHelp: gettext("Type in the handles (eg user@example.com) "
                    + "of the recipients. Separate by commas. Sorry, no search yet.."),
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
            }
        },
        visibilityOptions() {
            return VISIBILITY_OPTIONS
        },
    },
    methods: {
        onPostForm() {
            throw new Error("`onPostForm` must be overriden")
        },
    },
}

export {publisherMixin, VISIBILITY_OPTIONS}
export default publisherMixin
