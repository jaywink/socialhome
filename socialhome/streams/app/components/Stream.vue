<template>
    <div>
        <div class="container-flex">
            <div v-show="$store.state.hasNewContent" class="new-content-container">
                <b-button @click.prenvent.stop="onNewContentClick" variant="link" class="new-content-load-link">
                    <b-badge pill variant="primary">
                        {{ $store.state.newContentLengh }} new posts available
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
                    class="grid-item"
                    v-masonry-tile
                    v-for="content in $store.getters.contentList"
                    :content-id="content.id"
                    :key="content.id"
                />
            </div>
        </div>
    </div>
</template>

<script>
import Vue from "vue"
import imagesLoaded from "vue-images-loaded"
import "streams/app/components/StreamElement.vue"
import PublicStampedElement from "streams/app/components/PublicStampedElement.vue"
import FollowedStampedElement from "streams/app/components/FollowedStampedElement.vue"
import TagStampedElement from "streams/app/components/TagStampedElement.vue"
import {newStreamStore, streamStoreOperations} from "streams/app/stores/streamStore"
import applicationStore from "streams/app/stores/applicationStore"


export default Vue.component("stream", {
    store: newStreamStore({modules: {applicationStore}}),
    directives: {imagesLoaded},
    components: {FollowedStampedElement, PublicStampedElement, TagStampedElement},
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
