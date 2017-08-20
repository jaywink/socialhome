<template>
    <div>
        <div v-html="htmlSafe"></div>
        <author-bar
            v-if="showAuthorBar"
            v-bind="author"
            :is-user-author="isUserAuthor"
            :is-user-local="isUserLocal"
            :current-browsing-profile-id="currentBrowsingProfileId"
            :is-user-authenticated="isUserAuthenticated"
        >
        </author-bar>
        <div class="grid-item-bar d-flex justify-content-start">
            <div class="mt-1">
                <a :ref="contentUrl" :data-content-id="id" :title="timestamp" class="grid-item-open-action">
                    {{ humanizedTimestamp }}
                </a>&nbsp;
                <span v-if="edited">{{ editedText }}</span>
                <div v-if="isUserAuthor">
                    <a :href="updateUrl">
                        <i class="fa fa-pencil" title="Update" aria-label="Update"></i>
                    </a>
                    <a :href="deleteUrl">
                        <i class="fa fa-remove" title="Delete" aria-label="Delete"></i>
                    </a>
                </div>
            </div>
            <div class="ml-auto grid-item-reactions mt-1">
                <div v-if="showShares" class="item-reaction">
                    <i class="fa fa-refresh" title="Shares" aria-label="Shares"></i>
                    <span class="item-reaction-counter">{{ sharesCount }}</span>
                </div>
                <div v-if="showReplies" class="item-reaction">
                    <span class="item-open-replies-action" :data-content-id="id">
                        <i class="fa fa-envelope" title="Replies" aria-label="Replies"></i>
                    </span>
                    <span class="item-reaction-counter">{{ childrenCount }}</span>
                </div>
            </div>
        </div>
        <div class="replies-container" :data-content-id="id"></div>
        <div v-if="isUserAuthenticated" class="content-actions hidden" :data-content-id="id">
            <b-button variant="secondary" :href="replyUrl">Reply</b-button>
        </div>
    </div>
</template>

<script>
import Vue from "vue"
import "streams/app/components/AuthorBar.vue"


export default Vue.component("stream-element", {
    props: {
        id: {type: Number, required: true},
        author: {type: Object, required: true},
        timestamp: {type: String, required: true},
        humanizedTimestamp: {type: String, required: true},
        htmlSafe: {type: String, required: true},
        contentUrl: {type: String, required: true},
        updateUrl: {type: String, required: true},
        deleteUrl: {type: String, required: true},
        replyUrl: {type: String, required: true},
        childrenCount: {type: Number, required: true},
        sharesCount: {type: Number, required: true},
        edited: {type: Boolean, required: true},
        isUserLocal: {type: Boolean, required: true},
        isUserAuthor: {type: Boolean, required: true},
        showAuthorBar: {type: Boolean, required: true},
        isUserAuthenticated: {type: Boolean, required: true},
        currentBrowsingProfileId: {type: String, required: false},
    },
    computed: {
        editedText() {
            return this.edited ? " (edited)" : ""
        },
        showReplies() {
            return this.isUserAuthenticated || this.childrenCount > 0
        },
        showShares() {
            return this.isUserAuthenticated || this.sharesCount > 0
        },
    },
})
</script>
