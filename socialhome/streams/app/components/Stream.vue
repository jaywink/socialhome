<template>
    <div :class="{ container: this.$store.state.stream.single }">
        <div v-show="$store.getters.hasNewContent" class="new-content-container">
            <b-link @click.prevent.stop="onNewContentClick" class="new-content-load-link">
                <b-badge pill variant="primary">
                    {{ translations.newPostsAvailables }}
                </b-badge>
            </b-link>
        </div>
        <div v-if="this.$store.state.stream.single">
            <stream-element
                class="grid-item grid-item-full"
                :content="$store.getters.singleContent"
            />
        </div>
        <div v-else v-masonry v-bind="masonryOptions">
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
</template>


<script>
import Vue from "vue"

import VueScrollTo from "vue-scrollto"

import "streams/app/components/StreamElement.vue"
import PublicStampedElement from "streams/app/components/stamped_elements/PublicStampedElement.vue"
import FollowedStampedElement from "streams/app/components/stamped_elements/FollowedStampedElement.vue"
import TagStampedElement from "streams/app/components/stamped_elements/TagStampedElement.vue"
import ProfileStampedElement from "streams/app/components/stamped_elements/ProfileStampedElement.vue"
import "streams/app/components/LoadingElement.vue"

import {streamStoreOperations} from "streams/app/stores/streamStore"


Vue.use(VueScrollTo)

export default Vue.component("stream", {
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
            switch (this.$store.state.stream.name) {
                case "followed":
                    return "FollowedStampedElement"
                case "public":
                    return "PublicStampedElement"
                case "tag":
                    return "TagStampedElement"
                case "profile_all":
                case "profile_pinned":
                    return "ProfileStampedElement"
                default:
                    console.error(`Unsupported stream name ${this.$store.state.stream.name}`)
            }
        },
        translations() {
            const ln = this.unfetchedContentIds.length
            return {
                newPostsAvailables: ngettext(`${ln} new post available`, `${ln} new posts available`, ln),
            }
        },
        unfetchedContentIds() {
            return this.$store.state.unfetchedContentIds
        },
    },
    methods: {
        onNewContentClick() {
            this.$store.dispatch(streamStoreOperations.newContentAck).then(
                () => this.$nextTick( // Wait for new content to be rendered
                    () => this.$scrollTo("body")))
        },
    },
    beforeCreate() {
        if (!this.$store.state.stream.single) {
            this.$store.dispatch(streamStoreOperations.loadStream)
        }
    },
})
</script>


<style scoped lang="scss">
    @media all and (max-width: 1200px) {
        .container {
            width: 100%;
            max-width: unset;
            padding-left: 0;
            padding-right: 0;
        }
    }
    .new-content-load-link {
        cursor: pointer;
    }
</style>
