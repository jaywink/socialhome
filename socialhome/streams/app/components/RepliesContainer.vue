<template>
    <div v-images-loaded.on.progress="onImageLoad">
        <div class="replies-container">
            <stream-element
                class="reply"
                v-for="reply in replies"
                :content="reply"
                :key="reply.id"
            />
        </div>
        <div v-show="showSpinner" class="replies-spinner text-center">
            <i class="fa fa-spinner fa-spin fa-2x" aria-hidden="true"></i>
        </div>
        <div v-if="showReplyButton" class="content-actions">
            <b-button @click.prevent.stop="showReplyEditor" variant="secondary">{{ translations.reply }}</b-button>
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
import Vue from "vue"

import {streamStoreOperations} from "streams/app/stores/streamStore.operations";
import "streams/app/components/ReplyEditor.vue"


export default Vue.component("replies-container", {
    directives: {imagesLoaded},
    props: {
        content: {type: Object, required: true},
    },
    data() {
        return {
            replyEditorActive: false,
        }
    },
    computed: {
        isContent() {
            return this.content.content_type === "content"
        },
        isUserAuthenticated() {
            return this.$store.state.applicationStore.isUserAuthenticated
        },
        replies() {
            return this.$store.getters.replies(this.content)
        },
        shares() {
            return this.$store.getters.shares(this.content.id)
        },
        showReplyButton() {
            if (!this.isUserAuthenticated || this.replyEditorActive || (
                    this.$store.state.pending.replies && this.content.reply_count > 0)) {
                return false
            }
            if (this.content.content_type === "content") {
                return true
            } else if (this.content.content_type === "share" && this.content.reply_count > 0 ) {
                return true
            }
            return false
        },
        showSpinner() {
            return this.isContent && this.$store.state.pending.replies && this.content.reply_count > 0
        },
        translations() {
            return {
                reply: this.isContent ? gettext("Reply") : gettext("Reply to share"),
            }
        },
    },
    methods: {
        onImageLoad() {
            if (!this.$store.state.stream.single) {
                Vue.redrawVueMasonry()
            }
        },
        showReplyEditor() {
            this.replyEditorActive = true
        },
    },
    mounted() {
        if (this.isContent) {
            this.$store.dispatch(streamStoreOperations.getReplies, { params: { id: this.content.id } })
            this.$store.dispatch(streamStoreOperations.getShares, { params: { id: this.content.id } })
        }
    },
    updated() {
        if (!this.$store.state.stream.single) {
            Vue.redrawVueMasonry()
        }
    },
})
</script>


<style scoped>
    .replies-spinner {
        height: 42px;
    }
</style>
