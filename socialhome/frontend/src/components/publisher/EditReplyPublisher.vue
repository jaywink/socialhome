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
        postFormRequest() {
            const payload = {
                ...this.model,
                contentId: this.contentId,
                parent: this.parentId,
            }

            return this.$store.dispatch("publisher/editReply", payload)
        },
    },
}
</script>
