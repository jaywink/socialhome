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
        <div class="grid-item-bar d-flex justify-content-start">
            <div class="mt-1">
                <b-button :href="contentUrl" :title="timestamp">
                    {{ humanizedTimestamp }}<span v-if="edited"> {{ editedText }}</span>
                </b-button>
                <div v-if="isUserAuthor">
                    <b-button :href="updateUrl">
                        <i class="fa fa-pencil" title="Update" aria-label="Update"></i>
                    </b-button>
                    <b-button :href="deleteUrl">
                        <i class="fa fa-remove" title="Delete" aria-label="Delete"></i>
                    </b-button>
                </div>
            </div>
        </div>
        <stream-element-reactions-bar
            :id="id"
            :replies-count="repliesCount"
            :shares-count="sharesCount"
            :has-shared="hasShared"
        />
    </div>
</template>

<script>
import Vue from "vue"
import "streams/app/components/AuthorBar.vue"
import "streams/app/components/StreamElementReactionsBar.vue"
import store from "streams/app/stores/globalStore"


export default Vue.component("stream-element", {
    store,
    props: {
        id: {type: Number, required: true},
        author: {type: Object, required: true},
        timestamp: {type: String, required: true},
        humanizedTimestamp: {type: String, required: true},
        htmlSafe: {type: String, required: true},
        contentUrl: {type: String, required: true},
        updateUrl: {type: String, required: true},
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
        deleteUrl(){

        }
    },
    updated() {
        Vue.redrawVueMasonry()
    },
})
</script>
