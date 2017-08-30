<template>
    <div>
        <div v-html="htmlSafe"></div>
        <author-bar
            v-if="showAuthorBar"
            v-bind="author"
            :is-user-author="isUserAuthor"
            :is-user-local="isUserLocal"
        >
        </author-bar>
        <reactions-bar
            :id="id"
            :replies-count="repliesCount"
            :shares-count="sharesCount"
            :has-shared="hasShared"
        >
            <div class="mt-1">
                <a :href="contentUrl" :title="timestamp" class="unstyled-link">
                    {{ humanizedTimestamp }}<span v-if="edited"> {{ editedText }}</span>
                </a>
                &nbsp;
                <template v-if="isUserAuthor">
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
    store,
    props: {
        id: {type: Number, required: true},
        author: {type: Object, required: true},
        timestamp: {type: String, required: true},
        humanizedTimestamp: {type: String, required: true},
        htmlSafe: {type: String, required: true},
        contentUrl: {type: String, required: true},
        repliesCount: {type: Number, required: true},
        sharesCount: {type: Number, required: true},
        edited: {type: Boolean, required: true},
        isUserLocal: {type: Boolean, required: true},
        isUserAuthor: {type: Boolean, required: true},
        showAuthorBar: {type: Boolean, required: true},
        hasShared: {type: Boolean, required: true},
    },
    computed: {
        editedText() {
            return this.edited ? " (edited)" : ""
        },
        deleteUrl() {
            return Urls["content:delete"]({pk: this.id})
        },
        updateUrl() {
            return Urls["content:update"]({pk: this.id})
        },
    },
    updated() {
        Vue.redrawVueMasonry()
    },
})
</script>
