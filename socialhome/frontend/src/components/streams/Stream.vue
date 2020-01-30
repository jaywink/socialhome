<template>
    <div :class="{ container: streamDetails.single }">
        <div v-show="$store.getters['stream/hasNewContent']" class="new-content-container">
            <b-link class="new-content-load-link" @click.prevent.stop="onNewContentClick">
                <b-badge pill variant="primary">
                    {{ translations.newPostsAvailables }}
                </b-badge>
            </b-link>
        </div>
        <div v-if="streamDetails.single">
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
import {STREAM_NAMES} from "@/utils/constants"
import {streamLoadableMixin} from "@/components/streams/stream-loadable-mixin"

export default Vue.component("stream", {
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
    mixins: [streamLoadableMixin],
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
                case STREAM_NAMES.FOLLOWED:
                    return "FollowedStampedElement"
                case STREAM_NAMES.LIMITED:
                    return "LimitedStampedElement"
                case STREAM_NAMES.LOCAL:
                    return "LocalStampedElement"
                case STREAM_NAMES.PUBLIC:
                    return "PublicStampedElement"
                case STREAM_NAMES.TAG:
                    return "TagStampedElement"
                case STREAM_NAMES.TAGS:
                    return "TagsStampedElement"
                case STREAM_NAMES.PROFILE_ALL:
                case STREAM_NAMES.PROFILE_PINNED:
                    return "ProfileStampedElement"
                default:
                    // eslint-disable-next-line no-console
                    console.error(`Unsupported stream name ${this.streamName}`)
                    return ""
            }
        },
        translations() {
            const ln = this.unfetchedContentIds.length
            return {newPostsAvailables: ngettext(`${ln} new post available`, `${ln} new posts available`, ln)}
        },
        unfetchedContentIds() {
            return this.$store.state.stream.unfetchedContentIds
        },
    },
    beforeMount() {
        if (!this.streamDetails.single) {
            this.loadStream()
        }
    },
    methods: {
        onNewContentClick() {
            this.$store.dispatch("stream/newContentAck").then(
                () => this.$nextTick( // Wait for new content to be rendered
                    () => this.$scrollTo("body"),
                ),
            )
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
