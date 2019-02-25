<template>
    <div>
        <div class="grid-item-bar d-flex justify-content-start">
            <slot />
            <div class="ml-auto grid-item-reactions mt-1">
                <b-button
                    v-if="showShareReactionIcon"
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
                    v-if="showReplyReactionIcon"
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
        <div v-if="showRepliesContainer">
            <replies-container :content="content" />
        </div>
    </div>
</template>

<script>
import Vue from "vue"

import "frontend/components/streams/RepliesContainer.vue"


export default Vue.component("reactions-bar", {
    props: {
        content: {type: Object, required: true},
    },
    data() {
        return {
            showSharesBox: false,
            showRepliesBox: false,
        }
    },
    computed: {
        showRepliesContainer() {
            return this.showRepliesBox || this.$store.state.stream.stream.single
        },
        showReplyReactionIcon() {
            if (this.content.content_type === "content") {
                return this.$store.state.application.isUserAuthenticated || this.content.reply_count > 0
            }
            return false
        },
        showShareReactionIcon() {
            if (this.content.content_type === "content") {
                return this.$store.state.application.isUserAuthenticated || this.content.shares_count > 0
            }
            return false
        },
        canShare() {
            return !this.content.user_is_author && this.content.visibility === "public"
        },
        translations() {
            return {
                share: gettext("Share"),
                unshare: gettext("Unshare"),
            }
        },
        urls() {
            return {
                share: Urls["api:content-share"]({pk: this.content.id}),
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
                this.$snotify.error(gettext("Unable to reshare own post"))
                return
            }
            if (!this.$store.state.application.isUserAuthenticated) {
                this.$snotify.error(gettext("You must be logged in to reshare"))
                return
            }

            this.$http.post(this.urls.share)
                .then(() => {
                    this.showSharesBox = false
                    this.content.shares_count += 1
                    this.content.user_has_shared = true
                })
                .catch(_ => this.$snotify.error(gettext("An error happened while resharing the content")))
        },
        unshare() {
            if (!this.canShare) {
                this.$snotify.error(gettext("Unable to unshare own post"))
                return
            }
            if (!this.$store.state.application.isUserAuthenticated) {
                this.$snotify.error(gettext("You must be logged in to unshare"))
                return
            }

            this.$http.delete(this.urls.share)
                .then(() => {
                    this.showSharesBox = false
                    this.content.shares_count -= 1
                    this.content.user_has_shared = false
                })
                .catch(_ => this.$snotify.error(gettext("An error happened while unsharing the content")))
        },
    },
    updated() {
        if (!this.$store.state.stream.stream.single) {
            Vue.redrawVueMasonry()
        }
    },
})
</script>
