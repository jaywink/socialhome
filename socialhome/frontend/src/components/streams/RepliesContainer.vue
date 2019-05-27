<template>
  <div v-images-loaded.on.progress="onImageLoad">
    <div class="replies-container">
      <stream-element
        v-for="reply in replies"
        :key="reply.id"
        class="reply"
        :content="reply"
      />
    </div>
    <div v-show="showSpinner" class="replies-spinner text-center">
      <i class="fa fa-spinner fa-spin fa-2x" aria-hidden="true" />
    </div>
    <div v-if="showReplyButton" class="content-actions">
      <b-button variant="outline-dark" @click.prevent.stop="showReplyEditor">
        {{ translations.reply }}
      </b-button>
    </div>
    <div v-if="replyEditorActive">
      <reply-editor :content-id="content.id" />
    </div>
    <div v-if="isContent">
      <div v-for="share in shares" :key="share.id">
        <replies-container :content="share" />
      </div>
    </div>
  </div>
</template>

<script>
import imagesLoaded from "vue-images-loaded"
import "@/components/streams/ReplyEditor.vue"
import "@/components/streams/StreamElement.vue"


export default {
    name: "RepliesContainer",
    directives: {imagesLoaded},
    props: {content: {type: Object, required: true}},
    data() {
        return {replyEditorActive: false}
    },
    computed: {
        isContent() {
            return this.content.content_type === "content"
        },
        isUserAuthenticated() {
            return this.$store.state.application.isUserAuthenticated
        },
        replies() {
            return this.$store.getters["stream/replies"](this.content)
        },
        shares() {
            return this.$store.getters["stream/shares"](this.content.id)
        },
        showReplyButton() {
            if (!this.isUserAuthenticated || this.replyEditorActive || (
                this.$store.state.stream.pending.replies && this.content.reply_count > 0)) {
                return false
            }
            if (this.content.content_type === "content") {
                return true
            }
            return this.content.content_type === "share" && this.content.reply_count > 0
        },
        showSpinner() {
            return this.isContent && this.$store.state.stream.pending.replies && this.content.reply_count > 0
        },
        translations() {
            return {reply: this.isContent ? gettext("Reply") : gettext("Reply to share")}
        },
    },
    mounted() {
        if (this.isContent) {
            this.$store.dispatch("stream/getReplies", {params: {id: this.content.id}})
            this.$store.dispatch("stream/getShares", {params: {id: this.content.id}})
        }
    },
    updated() {
        if (!this.$store.state.stream.stream.single) {
            this.$redrawVueMasonry()
        }
    },
    methods: {
        onImageLoad() {
            if (!this.$store.state.stream.stream.single) {
                this.$redrawVueMasonry()
            }
        },
        showReplyEditor() {
            this.replyEditorActive = true
        },
    },
}
</script>

<style scoped>
  .replies-spinner {
    height: 42px;
  }
</style>
