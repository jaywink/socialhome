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
                        'button-no-pointer': content.user_is_author,
                    }"
                    class="item-reaction"
                    variant="outline-dark"
                    @click.stop.prevent="expandShares"
                >
                    <i class="fa fa-refresh" title="Shares" aria-label="Shares" />
                    <span class="item-reaction-counter">{{ content.shares_count }}</span>
                </b-button>
                <b-button
                    v-if="showReplyReactionIcon"
                    :class="{'item-reaction-counter-positive': content.reply_count}"
                    class="item-reaction"
                    variant="outline-dark"
                    @click.stop.prevent="expandComments"
                >
                    <span class="item-open-replies-action">
                        <i class="fa fa-comments" title="Replies" aria-label="Replies" />
                        <span class="item-reaction-counter">{{ content.reply_count }}</span>
                    </span>
                </b-button>
            </div>
        </div>
        <div v-if="canShare && showSharesBox" class="content-actions">
            <b-button v-if="content.user_has_shared" variant="outline-dark" @click.prevent.stop="unshare">
                {{ translations.unshare }}
            </b-button>
            <b-button v-else variant="outline-dark" @click.prevent.stop="share">
                {{ translations.share }}
            </b-button>
        </div>
        <div v-if="showRepliesContainer">
            <replies-container :content="content" />
        </div>
    </div>
</template>

<script>
import RepliesContainer from "@/components/streams/RepliesContainer.vue"


export default {
    name: "ReactionsBar",
    components: {RepliesContainer},
    props: {
        content: {
            type: Object, required: true,
        },
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
                return (
                    this.$store.state.application.isUserAuthenticated && !this.content.user_is_author
                ) || this.content.shares_count > 0
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
            return {share: Urls["api:content-share"]({pk: this.content.id})}
        },
    },
    updated() {
        if (!this.$store.state.stream.stream.single) {
            this.$redrawVueMasonry()
        }
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
                .catch(() => this.$snotify.error(gettext("An error happened while resharing the content")))
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
                .catch(() => this.$snotify.error(gettext("An error happened while unsharing the content")))
        },
    },
}
</script>
