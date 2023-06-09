<template>
    <div v-images-loaded.on.progress="onImageLoad">
        <div class="replies-container" v-bind:class="isReply?'vertical-bar':''" >
            <stream-element
                v-for="reply in replies"
                :key="reply.id"
                class="reply"
                :id="`r${reply.id}`"
                :content="reply"
            />
        </div>
        <div v-show="showSpinner" class="replies-spinner text-center">
            <i class="fa fa-spinner fa-spin fa-2x" aria-hidden="true" />
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
import "@/components/streams/StreamElement.vue"

export default {
    name: "RepliesContainer",
    directives: {imagesLoaded},
    props: {
        content: {
            type: Object, required: true,
        },
    },
    computed: {
        isContent() {
            return this.isPost || this.isReply
        },
        isPost() {
            return this.content.content_type === "content"
        },
        isReply() {
            return this.content.content_type === "reply"
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
        showSpinner() {
            // the vuex-rest-api pending property is global
            return this.isPost
                && this.$store.state.stream.pending.replies
                && this.content.reply_count > 0
        },
    },
    mounted() {
        if (this.isPost) {
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
    },
}
</script>

<style scoped>
  .replies-spinner {
    height: 42px;
  }
  .vertical-bar {
    border-left: 2px solid #373a3c;
  }
</style>
