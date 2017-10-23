<template>
    <div>
        <div
            v-if="isFifthLast"
            v-infinite-scroll="emitLoadMore"
            infinite-scroll-disabled="infiniteScrollDisabled"
        />
        <nsfw-shield v-if="content.is_nsfw" :tags="content.tags">
            <div v-html="content.rendered" />
        </nsfw-shield>
        <div v-else v-html="content.rendered" />

        <author-bar v-if="showAuthorBar" :content-id="contentId" />
        <reactions-bar :content-id="contentId">
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
import infiniteScroll from "vue-infinite-scroll"

import "streams/app/components/AuthorBar.vue"
import "streams/app/components/ReactionsBar.vue"
import "streams/app/components/NsfwShield.vue"


export default Vue.component("stream-element", {
    props: {
        contentId: {type: Number, required: true},
    },
    directives: {infiniteScroll},
    computed: {
        content() {
            return this.$store.state.contents[this.contentId]
        },
        deleteUrl() {
            return Urls["content:delete"]({pk: this.contentId})
        },
        infiniteScrollDisabled(){
            return this.$store.state.pending.contents || !this.$store.state.loadMore
        },
        isFifthLast() {
            return this.$store.state.contentIds[this.$store.state.contentIds.length - 5] === this.contentId
        },
        timestampText() {
            return this.content.edited
                ? `${this.content.humanized_timestamp} (${gettext("edited")})`
                : this.content.humanized_timestamp
        },
        showAuthorBar() {
            return this.$store.state.showAuthorBar
        },
        updateUrl() {
            return Urls["content:update"]({pk: this.contentId})
        },
    },
    methods: {
        emitLoadMore() {
            // Weirdly, this safeguard is necessary to prevent the infinite scroll
            // to load more content multiple times before the UI is refreshed
            if(this.isFifthLast){
                this.$emit("load-more")
            }
        },
    },
    updated() {
        Vue.redrawVueMasonry()
    },
})
</script>
