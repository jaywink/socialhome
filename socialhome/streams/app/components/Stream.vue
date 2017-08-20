<template>
    <div>
        <div class="container-flex">
            <div v-show="$store.state.stream.hasNewContent" class="new-content-container">
                <b-button @click.prenvent.stop="onNewContentClick" variant="link" class="new-content-load-link">
                    <b-badge pill variant="primary">
                        {{ $store.state.stream.newContentLengh }} new posts available
                    </b-badge>
                </b-button>
            </div>
            <div v-images-loaded.on.progress="onImageLoad" v-masonry v-bind="masonryOptions">
                <div class="stamped">
                    <stamped-element></stamped-element>
                </div>
                <div class="grid-sizer"></div>
                <div class="gutter-sizer"></div>
                <stream-element
                    class="grid-item"
                    v-for="content in $store.state.contentList"
                    v-bind="content"
                    v-masonry-tile
                    :key="content.id"
                    :is-user-authenticated="$store.state.isUserAuthenticated"
                    :show-author-bar="$store.state.showAuthorBar"
                    :current-browsing-profile-id="$store.state.currentBrowsingProfileId"
                >
                </stream-element>
            </div>
        </div>
    </div>
</template>

<script>
import Vue from "vue"
import imagesLoaded from "vue-images-loaded"
import "streams/app/components/StampedElement.vue"
import "streams/app/components/StreamElement.vue"
import {store, stateOperations} from "streams/app/stores/streamStore"


export default Vue.component("stream", {
    store,
    directives: {
        imagesLoaded,
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
    methods: {
        onImageLoad() {
            Vue.redrawVueMasonry()
        },
        onNewContentClick() {
            this.$store.dispatch(stateOperations.newContentAck)
        },
    },
})
</script>

<style scoped lang="scss">
    .new-content-load-link {
        cursor: pointer;
    }
</style>
