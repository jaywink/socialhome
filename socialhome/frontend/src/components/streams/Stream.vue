<template>
    <div :class="{ container: $store.state.stream.stream.single }">
        <div v-show="$store.getters['stream/hasNewContent']" class="new-content-container">
            <b-link class="new-content-load-link" @click.prevent.stop="onNewContentClick">
                <b-badge pill variant="primary">
                    {{ translations.newPostsAvailables }}
                </b-badge>
            </b-link>
        </div>
        <div v-if="$store.state.stream.stream.single">
            <stream-element class="grid-item grid-item-full" :content="singleContent" />
        </div>
        <div v-else>
            <div class="stamped">
                <component :is="stampedElement" />
            </div>
            <div
                v-if="showProfileStreamButtons"
                class="profile-stream-buttons"
            >
                <ProfileStreamButtons />
            </div>
            <div v-masonry class="grid" v-bind="masonryOptions">
                <div class="grid-sizer" />
                <div class="gutter-sizer" />
                <stream-element
                    v-for="content in $store.getters['stream/currentContentList']"
                    :key="content.id"
                    v-masonry-tile
                    class="grid-item"
                    :content="content"
                    @loadmore="loadStream"
                />
            </div>
        </div>
        <loading-element v-show="$store.state.stream.pending.contents" />
    </div>
</template>

<script>
import Vue from "vue"

import StreamElement from "@/components/streams/StreamElement.vue"
import PublicStampedElement from "@/components/streams/stamped_elements/PublicStampedElement.vue"
import FollowedStampedElement from "@/components/streams/stamped_elements/FollowedStampedElement.vue"
import LimitedStampedElement from "@/components/streams/stamped_elements/LimitedStampedElement.vue"
import LocalStampedElement from "@/components/streams/stamped_elements/LocalStampedElement.vue"
import TagStampedElement from "@/components/streams/stamped_elements/TagStampedElement.vue"
import TagsStampedElement from "@/components/streams/stamped_elements/TagsStampedElement.vue"
import ProfileStampedElement from "@/components/streams/stamped_elements/ProfileStampedElement.vue"
import LoadingElement from "@/components/common/LoadingElement.vue"
import ProfileStreamButtons from "@/components/streams/stamped_elements/ProfileStreamButtons"

export default Vue.component("Stream", {
    components: {
        FollowedStampedElement,
        LimitedStampedElement,
        LoadingElement,
        LocalStampedElement,
        ProfileStampedElement,
        ProfileStreamButtons,
        PublicStampedElement,
        StreamElement,
        TagStampedElement,
        TagsStampedElement,
    },
    provide() {
        const now = {}
        Object.defineProperty(now, "currentTime", {
            enumerable: true,
            get: () => this.currentTime,
        })
        return {now}
    },
    // TODO: Seperate Stream.vue into TagStream.vue, GuidProfile.vue and UsernameProfile.vue, etc. in the future
    props: {
        contentId: {
            type: String, default: "",
        },
        uuid: {
            type: String, default: "",
        },
        user: {
            type: String, default: "",
        },
        tag: {
            type: String, default: "",
        },
    },
    data() {
        return {
            masonryOptions: {
                "item-selector": ".grid-item",
                "column-width": ".grid-sizer",
                gutter: ".gutter-sizer",
                "percent-position": true,
                "transition-duration": "0s",
                stagger: 0,
            },
            currentTime: Date.now(),
        }
    },
    computed: {
        singleContent() {
            if (!this.$store.state.stream.singleContentId) {
                return null
            }
            return this.$store.state.stream.contents[this.$store.state.stream.singleContentId]
        },
        showProfileStreamButtons() {
            return this.streamName === "profile_all" || this.streamName === "profile_pinned"
        },
        stampedElement() {
            switch (this.streamName) {
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
                case "tags":
                    return "TagsStampedElement"
                case "profile_all":
                case "profile_pinned":
                    return "ProfileStampedElement"
                default:
                    // eslint-disable-next-line no-console
                    console.error(`Unsupported stream name ${this.streamName}`)
                    return ""
            }
        },
        streamName() {
            return this.$store.state.stream.stream.name
        },
        translations() {
            const ln = this.unfetchedContentIds.length
            const fmts = ngettext("%s new post available", "%s new posts available", ln)
            return {newPostsAvailables: interpolate(fmts, [ln])}
        },
        unfetchedContentIds() {
            return this.$store.state.stream.unfetchedContentIds
        },
    },
    beforeMount() {
        if (!this.$store.state.stream.stream.single) {
            this.loadStream()
        }
    },
    mounted() {
        this.nowTimer = setInterval(() => {
            this.currentTime = Date.now()
        }, 10000)
    },
    beforeDestroy() {
        clearInterval(this.nowTimer)
    },
    methods: {
        onNewContentClick() {
            this.$store.dispatch("stream/newContentAck").then(
                () => this.$nextTick( // Wait for new content to be rendered
                    () => this.$scrollTo("body"),
                ),
            )
        },
        loadStream() {
            const options = {params: {}}
            const lastContentId = this.$store.state.stream.currentContentIds[
                this.$store.state.stream.currentContentIds.length - 1
            ]
            if (lastContentId && this.$store.state.stream.contents[lastContentId]) {
                options.params.lastId = this.$store.state.stream.contents[lastContentId].through
            }

            switch (this.$store.state.stream.stream.name) {
                case "followed":
                    this.$store.dispatch("stream/getFollowedStream", options)
                    break
                case "limited":
                    this.$store.dispatch("stream/getLimitedStream", options)
                    break
                case "local":
                    this.$store.dispatch("stream/getLocalStream", options)
                    break
                case "public":
                    this.$store.dispatch("stream/getPublicStream", options)
                    break
                case "tag":
                    options.params.name = this.tag
                    this.$store.dispatch("stream/getTagStream", options)
                    break
                case "tags":
                    this.$store.dispatch("stream/getTagsStream", options)
                    break
                case "profile_all":
                    options.params.uuid = this.$store.state.application.profile.uuid
                    this.$store.dispatch("stream/getProfileAll", options)
                    break
                case "profile_pinned":
                    options.params.uuid = this.$store.state.application.profile.uuid
                    this.$store.dispatch("stream/getProfilePinned", options)
                    break
                default:
                    break
            }
        },
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
