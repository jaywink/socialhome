<template>
    <div>
        <div class="grid-item-bar d-flex justify-content-start">
            <slot />
            <div class="ml-auto grid-item-reactions mt-1">
                <b-button
                    v-if="showShares"
                    :class="{'item-reaction-shared': content.hasShared}"
                    class="item-reaction"
                    @click.stop.prevent="expandShares"
                >
                    <i class="fa fa-refresh" title="Shares" aria-label="Shares"></i>
                    <span class="item-reaction-counter">{{ content.sharesCount }}</span>
                </b-button>
                <b-button v-if="showReplies" class="item-reaction" @click.stop.prevent="expandComments">
                    <span class="item-open-replies-action">
                        <i class="fa fa-envelope" title="Replies" aria-label="Replies"></i>
                        <span class="item-reaction-counter">{{ content.repliesCount }}</span>
                    </span>
                </b-button>
            </div>
        </div>
        <div v-if="canShare && showSharesBox" class="content-actions">
            <b-button v-if="content.hasShared" variant="secondary" @click.prevent.stop="unshare">Unshare</b-button>
            <b-button v-else variant="secondary" @click.prevent.stop="share">Share</b-button>
        </div>
        <div class="replies-container"></div>
        <div v-if="showRepliesBox">
            <div v-if="$store.state.applicationStore.isUserAuthenticated" class="content-actions">
                <b-button :href="replyUrl" variant="secondary">Reply</b-button>
            </div>
        </div>
    </div>
</template>

<script>
import Vue from "vue"


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
            return this.$store.state.applicationStore.isUserAuthenticated || this.content.sharesCount > 0
        },
        showShares() {
            return this.canShare &&
                (this.$store.state.applicationStore.isUserAuthenticated || this.content.sharesCount > 0)
        },
        replyUrl() {
            return Urls["content:reply"]({pk: this.contentId})
        },
        canShare() {
            return !this.content.isUserAuthor
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
                    this.content.sharesCount += 1
                    this.content.hasShared = true
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
                    this.content.sharesCount -= 1
                    this.content.hasShared = false
                })
                .catch(err => console.error(err) /* TODO: Proper error handling */)
        },
    },
    updated() {
        Vue.redrawVueMasonry()
    },
})
</script>
