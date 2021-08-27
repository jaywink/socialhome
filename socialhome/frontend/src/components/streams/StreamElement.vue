<template>
    <div>
        <div v-if="content.hasLoadMore">
            <div v-infinite-scroll="loadMore" infinite-scroll-disabled="disableLoadMore" />
        </div>

        <author-bar v-if="showAuthorBar" :content="content" />

        <nsfw-shield v-if="content.is_nsfw" :tags="content.tags">
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div :id="`c${content.id}`" v-html="content.rendered" />
        </nsfw-shield>
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div v-else :id="`c${content.id}`" v-html="content.rendered" />

        <reactions-bar :content="content">
            <div v-if="!showAuthorBar" class="stream-element-content-timestamp mr-2">
                <content-timestamp :content="content" />
            </div>
            <div class="mt-1 grid-item-bar-links">
                <template v-if="content.user_is_author">
                    <a :href="updateUrl">
                        <i class="fa fa-pencil" :title="translations.update" :aria-label="translations.update" />
                    </a>
                    <a :href="deleteUrl">
                        <i class="fa fa-remove" :title="translations.delete" :aria-label="translations.delete" />
                    </a>
                </template>
            </div>
        </reactions-bar>
    </div>
</template>

<script>
import Vue from "vue"
import fitvids from "fitvids"

import AuthorBar from "@/components/streams/AuthorBar.vue"
import ContentTimestamp from "@/components/streams/ContentTimestamp"
import ReactionsBar from "@/components/streams/ReactionsBar.vue"
import NsfwShield from "@/components/streams/NsfwShield.vue"

const StreamElement = {
    name: "StreamElement",
    components: {
        ContentTimestamp, NsfwShield, ReactionsBar, AuthorBar,
    },
    props: {
        content: {
            type: Object, required: true,
        },
    },
    computed: {
        deleteUrl() {
            return Urls["content:delete"]({pk: this.content.id})
        },
        disableLoadMore() {
            return this.$store.state.stream.pending.contents || !this.content.hasLoadMore
        },
        showAuthorBar() {
            if (this.content.content_type === "reply") {
                // Always show author bar for replies
                return true
            }
            if (this.$store.state.application.isUserAuthenticated && !this.content.user_is_author) {
                // Always show if authenticated and not own content
                return true
            }
            // Fall back to central state
            return this.$store.state.stream.showAuthorBar
        },
        updateUrl() {
            return Urls["content:update"]({pk: this.content.id})
        },
        translations() {
            return {
                delete: gettext("Delete"),
                update: gettext("Update"),
            }
        },
    },
    mounted() {
        this.layoutAfterDOMChange()
        this.layoutAfterTwitterOEmbeds()
        if (this.content.show_preview) {
            fitvids(`#c${this.content.id}`)
        }
        if (!this.$store.state.stream.stream.single) {
            this.$redrawVueMasonry()
        }
    },
    updated() {
        if (!this.$store.state.stream.stream.single) {
            this.$redrawVueMasonry()
        }
    },
    methods: {
        layoutAfterDOMChange() {
            const post = document.getElementById(`c${this.content.id}`)
            if (post) {
                const redraw = this.$redrawVueMasonry
                // eslint-disable-next-line prefer-arrow-callback
                const resizeObs = new MutationObserver(() => {
                    redraw()
                })
                // eslint-disable-next-line object-curly-newline
                resizeObs.observe(post, {attributes: true, subtree: true, childList: true})
            }
        },
        layoutAfterTwitterOEmbeds() {
            // Hackity hack a Masonry redraw after hopefully Twitter oembeds are loaded...
            // Let's try only add these once even if we have many oembed's
            // Trigger also the actual widget load method since it's possible on
            // initial stream load it fires before Vue has time to render the widgets..
            if (this.content.has_twitter_oembed) {
                if (window.twttr.widgets !== undefined) {
                    // Trigger load now
                    window.twttr.widgets.load(document.getElementsByClassName(".streams-container")[0])
                } else {
                    // Wait a bit then!
                    setTimeout(() => {
                        window.twttr.widgets.load(document.getElementsByClassName(".streams-container")[0])
                    }, 1000)
                }
            }
        },
        loadMore() {
            this.$store.dispatch("stream/disableLoadMore", this.content.id)
            this.$emit("loadmore")
        },
    },
}

// StreamElement and RepliesContainer recursively source each other
// Global registration is needed to prevent StreamElement being unknown when redering StreamContainer
Vue.component(StreamElement.name, StreamElement)

export default StreamElement
</script>

<style lang="scss">
    .stream-element-content-timestamp, .grid-item-bar-links {
        align-self: center;
    }
</style>
