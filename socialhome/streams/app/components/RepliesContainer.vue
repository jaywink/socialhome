<template>
    <div>
        <div class="replies-container">
            <stream-element
                class="reply"
                v-for="reply in replies"
                :content-id="reply.id"
                :key="reply.id"
            />
        </div>
        <div v-if="isUserAuthenticated" class="content-actions">
            <b-button :href="replyUrl" variant="secondary">{{ translations.reply }}</b-button>
        </div>
        <div v-for="share in shares" :key="share.id">
            <div class="replies-container">
                <stream-element
                    class="reply"
                    v-for="reply in $store.getters.replies(share.id)"
                    :content-id="reply.id"
                    :key="reply.id"
                />
            </div>
            <div v-if="isUserAuthenticated" class="content-actions">
                <b-button :href="shareReplyUrl(share.id)" variant="secondary">{{ translations.shareReply }}</b-button>
            </div>
        </div>
    </div>
</template>


<script>
import Vue from "vue"

import {streamStoreOperations} from "streams/app/stores/streamStore.operations";


export default Vue.component("replies-container", {
    props: {
        contentId: {type: Number, required: true},
    },
    computed: {
        isUserAuthenticated() {
            return this.$store.state.applicationStore.isUserAuthenticated
        },
        replies() {
            return this.$store.getters.replies(this.contentId)
        },
        replyUrl() {
            return Urls["content:reply"]({pk: this.contentId})
        },
        shares() {
            return this.$store.getters.shares(this.contentId)
        },
        translations() {
            return {
                reply: gettext("Reply"),
                shareReply: gettext("Reply to share"),
            }
        },
    },
    methods: {
        shareReplyUrl: function(id) {
            return Urls["content:reply"]({pk: id})
        },
    },
    mounted() {
        this.$store.dispatch(streamStoreOperations.getReplies, {params: {id: this.contentId}})
        this.$store.dispatch(streamStoreOperations.getShares, {params: {id: this.contentId}})
    },
})
</script>
