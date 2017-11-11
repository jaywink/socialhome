<template>
    <div>
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
            <b-button :href="replyUrl" variant="secondary">{{ translations.reply }}</b-button>
        </div>
        <div v-if="isContent">
            <div v-for="share in shares" :key="share.id">
                <replies-container :content="share" />
            </div>
        </div>
    </div>
</template>


<script>
import Vue from "vue"

import {streamStoreOperations} from "streams/app/stores/streamStore.operations";


export default Vue.component("replies-container", {
    props: {
        content: {type: Object, required: true},
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
        replyUrl() {
            return Urls["content:reply"]({pk: this.content.id})
        },
        shares() {
            return this.$store.getters.shares(this.content.id)
        },
        showReplyButton() {
            if (!this.isUserAuthenticated || (this.$store.state.pending.replies && this.content.reply_count > 0)) {
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
    mounted() {
        if (this.isContent) {
            this.$store.dispatch(streamStoreOperations.getReplies, { params: { id: this.content.id } })
            this.$store.dispatch(streamStoreOperations.getShares, { params: { id: this.content.id } })
        }
    },
    updated() {
        Vue.redrawVueMasonry()
    },
})
</script>


<style scoped>
    .replies-spinner {
        height: 42px;
    }
</style>
