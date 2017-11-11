<template>
    <div>
        <nsfw-shield v-if="content.is_nsfw" :tags="content.tags">
            <div v-html="content.rendered" />
        </nsfw-shield>
        <div v-else v-html="content.rendered" />

        <author-bar v-if="showAuthorBar" :content="content" />
        <reactions-bar :content="content">
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
import "streams/app/components/NsfwShield.vue"


export default Vue.component("stream-element", {
    props: {
        content: {type: Object, required: true},
    },
    computed: {
        deleteUrl() {
            return Urls["content:delete"]({pk: this.content.id})
        },
        timestampText() {
            return this.content.edited
                ? `${this.content.humanized_timestamp} (${gettext("edited")})`
                : this.content.humanized_timestamp
        },
        showAuthorBar() {
            if (this.content.content_type === "reply") {
                // Always show author bar for replies
                return true
            } else if (this.$store.state.applicationStore.isUserAuthenticated && !this.content.user_is_author) {
                // Always show if authenticated and not own content
                return true
            }
            // Fall back to central state
            return this.$store.state.showAuthorBar
        },
        updateUrl() {
            return Urls["content:update"]({pk: this.content.id})
        },
    },
    updated() {
        Vue.redrawVueMasonry()
    },
})
</script>
