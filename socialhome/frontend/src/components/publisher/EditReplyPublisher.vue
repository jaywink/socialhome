<script>
import ReplyPublisher from "@/components/publisher/ReplyPublisher"


export default {
    name: "EditReplyPublisher",
    extends: ReplyPublisher,
    props: {
        contentId: {
            type: String, required: true,
        },
        parentId: {
            type: String, required: true,
        },
        showPreview: {
            type: Boolean, default: true,
        },
        text: {
            type: String, required: true,
        },
    },
    computed: {
        titleText() {
            return this.translations.updateReply
        },
    },
    beforeMount() {
        this.baseModel.text = this.text
        this.baseModel.showPreview = this.showPreview
    },
    methods: {
        onPostForm() {
            this.$store.dispatch("publisher/editReply", {
                ...this.model,
                contentId: this.contentId,
                parent: this.parentId,
            })
                .then(url => window.location.replace(url))
                .catch(() => this.$snotify.error(this.translations.postUploadError, {timeout: 10000}))
        },
    },
}
</script>
