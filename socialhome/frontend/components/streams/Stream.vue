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
                :content="singleContent"
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
                @loadmore="loadStream"
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

import {streamStoreOperations} from "frontend/stores/streamStore"

import "frontend/components/streams/StreamElement.vue"
import PublicStampedElement from "frontend/components/streams/stamped_elements/PublicStampedElement.vue"
import FollowedStampedElement from "frontend/components/streams/stamped_elements/FollowedStampedElement.vue"
import LimitedStampedElement from "frontend/components/streams/stamped_elements/LimitedStampedElement.vue"
import LocalStampedElement from "frontend/components/streams/stamped_elements/LocalStampedElement.vue"
import TagStampedElement from "frontend/components/streams/stamped_elements/TagStampedElement.vue"
import ProfileStampedElement from "frontend/components/streams/stamped_elements/ProfileStampedElement.vue"
import "frontend/components/streams/LoadingElement.vue"


Vue.use(VueScrollTo)

export default Vue.component("stream", {
    // TODO: Seperate Stream.vue into TagStream.vue, GuidProfile.vue and UsernameProfile.vue, etc. in the future
    props: {
        contentId: {type: String, default: ""},
        uuid: {type: String, default: ""},
        user: {type: String, default: ""},
        tag: {type: String, default: ""},
    },
    components: {
        FollowedStampedElement,
        LimitedStampedElement,
        LocalStampedElement,
        ProfileStampedElement,
        PublicStampedElement,
        TagStampedElement,
    },
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
        singleContent() {
            if (!this.$store.state.singleContentId) {
                return null
            }
            return this.$store.state.contents[this.$store.state.singleContentId]
        },
        stampedElement() {
            switch (this.$store.state.stream.name) {
                case "followed":
                    return "FollowedStampedElement"
                case "limited":
                    return "LimitedStampedElement"
                case "local":
                    return "LocalStampedElement"
                case "public":
                    return "PublicStampedElement"
                case "tag":
                    return "TagStampedElement"
                case "profile_all":
                case "profile_pinned":
                    return "ProfileStampedElement"
                default:
                    console.error(`Unsupported stream name ${this.$store.state.stream.name}`)
                    return ""
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
        loadStream() {
            const options = {params: {}}
            const lastContentId = this.$store.state.contentIds[this.$store.state.contentIds.length - 1]
            if (lastContentId && this.$store.state.contents[lastContentId]) {
                options.params.lastId = this.$store.state.contents[lastContentId].through
            }

            switch (this.$store.state.stream.name) {
                case "followed":
                    this.$store.dispatch(streamStoreOperations.getFollowedStream, options)
                    break
                case "limited":
                    this.$store.dispatch(streamStoreOperations.getLimitedStream, options)
                    break
                case "local":
                    this.$store.dispatch(streamStoreOperations.getLocalStream, options)
                    break
                case "public":
                    this.$store.dispatch(streamStoreOperations.getPublicStream, options)
                    break
                case "tag":
                    options.params.name = this.tag
                    this.$store.dispatch(streamStoreOperations.getTagStream, options)
                    break
                case "profile_all":
                    // TODO: Replace this with uuid property when API has evolved to support uuid
                    options.params.id = this.$store.state.applicationStore.profile.id
                    this.$store.dispatch(streamStoreOperations.getProfileAll, options)
                    break
                case "profile_pinned":
                    // TODO: Replace this with uuid property when API has evolved to support uuid
                    options.params.id = this.$store.state.applicationStore.profile.id
                    this.$store.dispatch(streamStoreOperations.getProfilePinned, options)
                    break
                default:
                    break
            }
        },
    },
    beforeMount() {
        if (!this.$store.state.stream.single) {
            this.loadStream()
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
