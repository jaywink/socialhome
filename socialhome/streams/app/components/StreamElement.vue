<template>
    <div>
        <div v-html="content.rendered"></div>
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
import "streams/app/components/AuthorBar.vue"
import "streams/app/components/ReactionsBar.vue"
import store from "streams/app/stores/applicationStore"


export default Vue.component("stream-element", {
    props: {
        contentId: {type: Number, required: true},
    },
    computed: {
        content() {
            return this.$store.state.contents[this.contentId]
        },
        deleteUrl() {
            return Urls["content:delete"]({pk: this.contentId})
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
    updated() {
        Vue.redrawVueMasonry()
    },
})
</script>
