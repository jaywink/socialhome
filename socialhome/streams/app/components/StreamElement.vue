<template>
    <div v-images-loaded.on.progress="onImageLoad" >
        <div v-if="content.hasLoadMore">
            <div v-infinite-scroll="loadMore" infinite-scroll-disabled="disableLoadMore"></div>
        </div>

        <nsfw-shield v-if="content.is_nsfw" :tags="content.tags">
            <div v-html="content.rendered" />
        </nsfw-shield>
        <div v-else v-html="content.rendered" />

        <author-bar v-if="showAuthorBar" :content="content" />
        <reactions-bar :content="content">
            <div class="mt-1">
                <a :href="content.url" :title="content.timestamp" class="unstyled-link">
                    {{ timestampText }}
                </a>
                &nbsp;
                <template v-if="content.user_is_author">
                    <a :href="updateUrl">
                        <i class="fa fa-pencil" title="Update" aria-label="Update"></i>
                    </a>
                    &nbsp;
                    <a :href="deleteUrl">
                        <i class="fa fa-remove" title="Delete" aria-label="Delete"></i>
                    </a>
                </template>
            </div>
        </reactions-bar>
    </div>
</template>

<script>
import Vue from "vue"
import imagesLoaded from "vue-images-loaded"

import {streamStoreOperations} from "streams/app/stores/streamStore.operations"
import "streams/app/components/AuthorBar.vue"
import "streams/app/components/ReactionsBar.vue"
import "streams/app/components/NsfwShield.vue"


export default Vue.component("stream-element", {
    directives: {imagesLoaded},
    props: {
        content: {type: Object, required: true},
    },
    computed: {
        deleteUrl() {
            return Urls["content:delete"]({pk: this.content.id})
        },
        disableLoadMore() {
            return this.$store.state.pending.contents || ! this.content.hasLoadMore
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
            } else if (this.$store.state.applicationStore.isUserAuthenticated && !this.content.user_is_author) {
                // Always show if authenticated and not own content
                return true
            }
            // Fall back to central state
            return this.$store.state.showAuthorBar
        },
        updateUrl() {
            return Urls["content:update"]({pk: this.content.id})
        },
    },
    methods: {
        initTwitterOEmbed() {
            // Fetch Twitter script and init embed when updated.
            // Adapted from: https://gist.github.com/fahrenq/0e815fef2bd296f2e9a061cc27e5a27b
            (function (d, s, id, c) {
                let js
                let fjs = d.getElementsByTagName(s)[0]
                if (fjs === undefined) return
                let t = window.twttr || {}
                if (d.getElementById(id) && t.widgets !== undefined) {
                    if (t.events._handlers === undefined || t.events._handlers.loaded.length === 0) {
                        // Bind a tweet loaded event for images loaded, but only once
                        t.events.bind('loaded', () => {
                            c.onImageLoad()
                        })
                    }
                    // Init embeds
                    return t.widgets.load();
                }
                // Fetch script to window
                js = d.createElement(s)
                js.id = id
                js.src = "https://platform.twitter.com/widgets.js"
                if (d.getElementById(id)) return  // Try not to load JS more than once
                fjs.parentNode.insertBefore(js, fjs)
                t._e = []
                t.ready = function (f) {
                    t._e.push(f)
                  }
                return t;
            }(document, "script", "twitter-wjs", this))
        },
        loadMore() {
            this.$store.dispatch(streamStoreOperations.disableLoadMore, this.content.id)
            this.$store.dispatch(streamStoreOperations.loadStream)
        },
        onImageLoad() {
            if (!this.$store.state.stream.single) {
                Vue.redrawVueMasonry()
            }
        },
    },
    mounted() {
        this.initTwitterOEmbed()
    },
    updated() {
        if (!this.$store.state.stream.single) {
            Vue.redrawVueMasonry()
        }
    },
})
</script>
