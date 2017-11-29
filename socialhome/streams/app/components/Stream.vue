<template>
    <div>
        <div class="container-flex">
            <div v-show="$store.state.hasNewContent" class="new-content-container">
                <b-link @click.prevent.stop="onNewContentClick" class="new-content-load-link">
                    <b-badge pill variant="primary">
                        {{ $store.state.newContentLengh }} new posts available
                    </b-badge>
                </b-link>
            </div>
            <div v-images-loaded.on.progress="onImageLoad" v-masonry v-bind="masonryOptions">
                <div class="stamped">
                    <component :is="stampedElement" />
                </div>
                <div class="grid-sizer"></div>
                <div class="gutter-sizer"></div>
                <stream-element
                    class="grid-item"
                    v-masonry-tile
                    v-for="content in $store.getters.contentList"
                    :content="content"
                    :key="content.id"
                />
            </div>
            <loading-element v-show="$store.state.pending.contents" />
        </div>
    </div>
</template>

<script>
import Vue from "vue"
import imagesLoaded from "vue-images-loaded"
import "streams/app/components/StreamElement.vue"
import PublicStampedElement from "streams/app/components/stamped_elements/PublicStampedElement.vue"
import FollowedStampedElement from "streams/app/components/stamped_elements/FollowedStampedElement.vue"
import TagStampedElement from "streams/app/components/stamped_elements/TagStampedElement.vue"
import ProfileStampedElement from "streams/app/components/stamped_elements/ProfileStampedElement.vue"
import "streams/app/components/LoadingElement.vue"
import {newStreamStore, streamStoreOperations} from "streams/app/stores/streamStore"
import applicationStore from "streams/app/stores/applicationStore"


export default Vue.component("stream", {
    store: newStreamStore({modules: {applicationStore}}),
    directives: {imagesLoaded},
    components: {FollowedStampedElement, PublicStampedElement, ProfileStampedElement, TagStampedElement},
    data() {
        return {
            masonryOptions: {
                "item-selector": ".grid-item",
                "column-width": ".grid-sizer",
                gutter: ".gutter-sizer",
                "percent-position": true,
                stamp: ".stamped",
                "transition-duration": "0s",
                stagger: 0,
            },
        }
    },
    computed: {
        stampedElement() {
            if (this.$store.state.streamName.match(/^followed/)) {
                return "FollowedStampedElement"
            } else if (this.$store.state.streamName.match(/^public/)) {
                return "PublicStampedElement"
            } else if (this.$store.state.streamName.match(/^tag/)) {
                return "TagStampedElement"
            } else if (this.$store.state.streamName.match(/^profile/)) {
                return "ProfileStampedElement"
            } else {
                console.error(`Unsupported stream name ${this.$store.state.streamName}`)
            }
        },
    },
    methods: {
        onImageLoad() {
            Vue.redrawVueMasonry()
        },
        onNewContentClick() {
            this.$store.dispatch(streamStoreOperations.newContentAck)
        },
    },
    beforeCreate() {
        this.$store.dispatch(streamStoreOperations.loadStream)
    },
    beforeDestroy() {
        this.$store.$websocket.close()
    },
    updated() {
        // Fetch Twitter script and init embeds when updated.
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
            fjs.parentNode.insertBefore(js, fjs)
            t._e = []
            t.ready = function (f) {
                t._e.push(f)
              }
            return t;
        }(document, "script", "twitter-wjs", this))
    },
})
</script>

<style scoped lang="scss">
    .new-content-load-link {
        cursor: pointer;
    }
</style>
