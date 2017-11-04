<template>
    <div>
        <div class="container-flex">
            <div v-show="$store.getters.hasNewContent" class="new-content-container">
                <b-button @click.prenvent.stop="onNewContentClick" variant="link" class="new-content-load-link">
                    <b-badge pill variant="primary">
                        {{ translations.newPostsAvailables }}
                    </b-badge>
                </b-button>
            </div>
            <div v-images-loaded.on.progress="onImageLoad" v-masonry v-bind="masonryOptions">
                <div class="stamped">
                    <component :is="stampedElement" />
                </div>
                <div class="grid-sizer"></div>
                <div class="gutter-sizer"></div>
                <stream-element
                    v-masonry-tile
                    v-for="id in $store.state.contentIds"
                    @load-more="loadMore"
                    :content-id="id"
                    :key="id"
                    class="grid-item"
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
        currentBrowsingProfileId() {
            return this.$store.state.applicationStore.currentBrowsingProfileId
        },
        translations() {
            return {
                newPostsAvailables: interpolate(
                    ngettext("%s new post available", "%s new posts available", this.unfetchedContentIds.length),
                    [this.unfetchedContentIds.length]),
            }
        },
        unfetchedContentIds() {
            return this.$store.state.unfetchedContentIds
        },
    },
    methods: {
        loadMore() {
            let contentId = this.$store.state.contentIds.slice(-1)[0]
            if (contentId) {
                this.loadStream(this.$store.state.contents[contentId].through)
            }
        },
        loadStream(lastId = undefined) {
            if (!this.$store.state.loadMore) {
                return
            }

            let options = lastId ? {params: {lastId}} : {params: {}}

            if (this.$store.state.streamName.match(/^followed/)) {
                this.$store.dispatch(streamStoreOperations.getFollowedStream, options)
            } else if (this.$store.state.streamName.match(/^public/)) {
                this.$store.dispatch(streamStoreOperations.getPublicStream, options)
            } else if (this.$store.state.streamName.match(/^tag/)) {
                options.params.name = this.$store.state.tagName
                this.$store.dispatch(streamStoreOperations.getTagStream, options)
            } else if (this.$store.state.streamName.match(/^profile_all/)) {
                options.params.id = this.currentBrowsingProfileId
                this.$store.dispatch(streamStoreOperations.getProfileAll, options)
            } else if (this.$store.state.streamName.match(/^profile_pinned/)) {
                options.params.id = this.currentBrowsingProfileId
                this.$store.dispatch(streamStoreOperations.getProfilePinned, options)
            }
        },
        onImageLoad() {
            Vue.redrawVueMasonry()
        },
        onNewContentClick() {
            this.$store.dispatch(streamStoreOperations.newContentAck)
        },
    },
    created() {
        this.loadStream()
    },
    beforeDestroy() {
        this.$store.$websocket.close()
    },
})
</script>

<style scoped lang="scss">
    .new-content-load-link {
        cursor: pointer;
    }
</style>
