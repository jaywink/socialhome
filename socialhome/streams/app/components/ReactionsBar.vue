<template>
    <div>
        <div class="grid-item-bar d-flex justify-content-start">
            <slot />
            <div class="ml-auto grid-item-reactions mt-1">
                <b-button
                    v-if="showShares"
                    :class="{
                        'item-reaction-shared': content.user_has_shared,
                        'item-reaction-counter-positive': content.shares_count,
                    }"
                    class="item-reaction"
                    @click.stop.prevent="expandShares"
                >
                    <i class="fa fa-refresh" title="Shares" aria-label="Shares"></i>
                    <span class="item-reaction-counter">{{ content.shares_count }}</span>
                </b-button>
                <b-button
                    v-if="showReplies"
                    :class="{'item-reaction-counter-positive': content.reply_count}"
                    class="item-reaction"
                    @click.stop.prevent="expandComments"
                >
                    <span class="item-open-replies-action">
                        <i class="fa fa-comments" title="Replies" aria-label="Replies"></i>
                        <span class="item-reaction-counter">{{ content.reply_count }}</span>
                    </span>
                </b-button>
            </div>
        </div>
        <div v-if="canShare && showSharesBox" class="content-actions">
            <b-button v-if="content.user_has_shared" variant="secondary" @click.prevent.stop="unshare">
                {{ translations.unshare }}
            </b-button>
            <b-button v-else variant="secondary" @click.prevent.stop="share">{{ translations.share }}</b-button>
        </div>
        <div v-if="showRepliesBox">
            <replies-container :content-id="content.id" />
        </div>
    </div>
</template>

<script>
import Vue from "vue"

import "streams/app/components/RepliesContainer.vue"


export default Vue.component("reactions-bar", {
    props: {
        contentId: {type: Number, required: true},
    },
    data() {
        return {
            showSharesBox: false,
            showRepliesBox: false,
        }
    },
    computed: {
        content() {
            return this.$store.state.contents[this.contentId]
        },
        showReplies() {
            return this.$store.state.applicationStore.isUserAuthenticated || this.content.reply_count > 0
        },
        showShares() {
            return this.$store.state.applicationStore.isUserAuthenticated || this.content.shares_count > 0
        },
        canShare() {
            return !this.content.user_is_author
        },
        translations() {
            return {
                share: gettext("Share"),
                unshare: gettext("Unshare"),
            }
        },
    },
    methods: {
        expandComments() {
            this.showRepliesBox = !this.showRepliesBox
        },
        expandShares() {
            this.showSharesBox = !this.showSharesBox
        },
        share() {
            if (!this.canShare) {
                console.error("Unable to share own post")
                return
            }
            if (!this.$store.state.applicationStore.isUserAuthenticated) {
                console.error("Not logged in")
                return
            }
            this.$http.post(`/api/content/${this.contentId}/share/`)
                .then(() => {
                    this.showSharesBox = false
                    this.content.shares_count += 1
                    this.content.user_has_shared = true
                })
                .catch(err => console.error(err) /* TODO: Proper error handling */)
        },
        unshare() {
            if (!this.canShare) {
                console.error("Unable to unshare own post")
                return
            }
            if (!this.$store.state.applicationStore.isUserAuthenticated) {
                console.error("Not logged in")
                return
            }
            this.$http.delete(`/api/content/${this.contentId}/share/`)
                .then(() => {
                    this.showSharesBox = false
                    this.content.shares_count -= 1
                    this.content.user_has_shared = false
                })
                .catch(err => console.error(err) /* TODO: Proper error handling */)
        },
    },
    updated() {
        Vue.redrawVueMasonry()
    },
})
</script>
