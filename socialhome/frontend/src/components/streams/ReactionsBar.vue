<template>
    <div>
        <div class="grid-item-bar d-flex justify-content-start">
            <slot />
            <reply-button
                v-if="content.content_type === 'content'"
                :content-type="content.content_type"
                :toggle-reply-editor="toggleReplyEditor"
            />
            <share-button
                v-if="content.content_type === 'content'"
                :content="content"
            />
            <div class="ml-auto grid-item-reactions mt-1">
                <b-button
                    v-if="showShareReactionIcon"
                    variant="link"
                    class="reaction-icons button-no-pointer"
                >
                    <span :title="translations.shares" :aria-label="translations.shares">
                        <i class="fa fa-refresh" />
                        <span class="reaction-counter">{{ content.shares_count }}</span>
                    </span>
                </b-button>
                <b-button
                    v-if="showExpandRepliesIcon"
                    variant="link"
                    class="reaction-icons"
                    @click.stop.prevent="expandReplies"
                >
                    <span
                        class="item-open-replies-action"
                        :title="translations.replies"
                        :aria-label="translations.replies"
                    >
                        <i class="fa fa-comments" />
                        <span class="reaction-counter">{{ content.reply_count }}</span>
                    </span>
                </b-button>
                <reply-button
                    v-if="content.content_type === 'reply'"
                    :content-type="content.content_type"
                    :toggle-reply-editor="toggleReplyEditor"
                />
            </div>
        </div>
        <div v-if="replyEditorActive">
            <reply-editor
                :content-id="content.id"
                :content-visibility="content.visibility"
                :toggle-reply-editor="toggleReplyEditor"
            />
        </div>
        <div v-if="showRepliesContainer">
            <replies-container :content="content" />
        </div>
    </div>
</template>

<script>
import RepliesContainer from "@/components/streams/RepliesContainer.vue"
import ReplyButton from "@/components/buttons/ReplyButton"
import ReplyEditor from "@/components/streams/ReplyEditor"
import ShareButton from "@/components/buttons/ShareButton"

export default {
    name: "ReactionsBar",
    components: {
        ReplyButton,
        RepliesContainer,
        ReplyEditor,
        ShareButton,
    },
    props: {
        content: {
            type: Object, required: true,
        },
    },
    data() {
        return {
            showRepliesBox: false,
            replyEditorActive: false,
        }
    },
    computed: {
        showExpandRepliesIcon() {
            if (this.content.content_type === "content") {
                return this.content.reply_count > 0
            }
            return false
        },
        showRepliesContainer() {
            return this.showRepliesBox || this.$store.state.stream.stream.single
        },
        showShareReactionIcon() {
            if (this.content.content_type === "content") {
                return this.content.shares_count > 0
            }
            return false
        },
        translations() {
            return {
                replies: gettext("Replies"),
                shares: gettext("Shares"),
            }
        },
    },
    updated() {
        if (!this.$store.state.stream.stream.single) {
            this.$redrawVueMasonry()
        }
    },
    methods: {
        expandReplies() {
            this.showRepliesBox = !this.showRepliesBox
        },
        toggleReplyEditor() {
            this.replyEditorActive = !this.replyEditorActive
            if (!this.showRepliesBox) {
                this.expandReplies()
            }
        },
    },
}
</script>

<style type="text/scss" scoped>
  .reaction-counter {
    padding-left: 3px;
  }
</style>
