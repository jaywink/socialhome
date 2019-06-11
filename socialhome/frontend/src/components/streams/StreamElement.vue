<template>
  <div v-images-loaded.on.progress="onImageLoad">
    <div v-if="content.hasLoadMore">
      <div v-infinite-scroll="loadMore" infinite-scroll-disabled="disableLoadMore" />
    </div>

    <nsfw-shield v-if="content.is_nsfw" :tags="content.tags">
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div v-html="content.rendered" />
    </nsfw-shield>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div v-else v-html="content.rendered" />

    <author-bar v-if="showAuthorBar" :content="content" />
    <reactions-bar :content="content">
      <div class="mt-1 grid-item-bar-links">
        <a :href="content.url" :title="content.timestamp" class="unstyled-link">
          {{ timestampText }}
        </a>
        <i v-if="isLimited" class="fa fa-lock mr-2" aria-hidden="true" />

        <template v-if="content.user_is_author">
          <a :href="updateUrl">
            <i class="fa fa-pencil" title="Update" aria-label="Update" />
          </a>
          <a :href="deleteUrl">
            <i class="fa fa-remove" title="Delete" aria-label="Delete" />
          </a>
        </template>
      </div>
    </reactions-bar>
  </div>
</template>

<script>
import Vue from "vue"
import imagesLoaded from "vue-images-loaded"

import AuthorBar from "@/components/streams/AuthorBar.vue"
import ReactionsBar from "@/components/streams/ReactionsBar.vue"
import NsfwShield from "@/components/streams/NsfwShield.vue"


const StreamElement = {
    name: "StreamElement",
    directives: {imagesLoaded},
    components: {NsfwShield, ReactionsBar, AuthorBar},
    props: {content: {type: Object, required: true}},
    computed: {
        deleteUrl() {
            return Urls["content:delete"]({pk: this.content.id})
        },
        disableLoadMore() {
            return this.$store.state.stream.pending.contents || !this.content.hasLoadMore
        },
        isLimited() {
            return this.content.visibility === "limited"
        },
        timestampText() {
            return this.content.edited
                ? `${this.content.humanized_timestamp} (${gettext("edited")})`
                : this.content.humanized_timestamp
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
    },
    mounted() {
        this.layoutAfterTwitterOEmbeds()
    },
    updated() {
        if (!this.$store.state.stream.stream.single) {
            this.$redrawVueMasonry()
        }
    },
    methods: {
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
                if (this.$store.state.stream.layoutDoneAfterTwitterOEmbeds) {
                    return
                }
                this.$store.dispatch("stream/setLayoutDoneAfterTwitterOEmbeds", true)
                const c = this
                setTimeout(() => {
                    c.onImageLoad()
                }, 2000)
                setTimeout(() => {
                    c.onImageLoad()
                }, 4000)
            }
        },
        loadMore() {
            this.$store.dispatch("stream/disableLoadMore", this.content.id)
            this.$emit("loadmore")
        },
        onImageLoad() {
            if (!this.$store.state.stream.stream.single) {
                this.$redrawVueMasonry()
            }
        },
    },
}

// StreamElement and RepliesContainer recursively source each other
// Global registration is needed to prevent StreamElement being unknown when redering StreamContainer
Vue.component(StreamElement.name, StreamElement)

export default StreamElement
</script>
