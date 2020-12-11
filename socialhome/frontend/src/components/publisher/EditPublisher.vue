<script>
import Publisher from "@/components/publisher/Publisher"
import {VISIBILITY_OPTIONS} from "@/components/publisher/publisher-mixin"

export default {
    name: "EditPublisher",
    extends: Publisher,
    props: {
        contentId: {
            type: String, required: true,
        },
        federate: {
            type: Boolean, default: true,
        },
        includeFollowing: {
            type: Boolean, default: false,
        },
        pinned: {
            type: Boolean, default: false,
        },
        recipients: {
            type: Array, default: () => [],
        },
        showPreview: {
            type: Boolean, default: true,
        },
        text: {
            type: String, required: true,
        },
        visibility: {
            type: Number, default: VISIBILITY_OPTIONS.PUBLIC.value,
        },
    },
    computed: {
        titleText() {
            return this.translations.edit
        },
    },
    beforeMount() {
        this.baseModel.showPreview = this.showPreview
        this.baseModel.text = this.text
        this.extendedModel.federate = this.federate
        this.extendedModel.includeFollowing = this.includeFollowing
        this.extendedModel.pinned = this.pinned
        this.extendedModel.recipients = this.recipients
        this.extendedModel.visibility = this.visibility
    },
    methods: {
        postFormRequest() {
            const payload = {
                ...this.model,
                contentId: this.contentId,
            }

            return this.$store.dispatch("publisher/editPost", payload)
        },
    },
}
</script>
