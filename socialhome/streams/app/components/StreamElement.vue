<template>
    <div>
        <div v-html="htmlSafe"></div>
        <author-bar
            v-if="showAuthorBar"
            v-bind="author"
            :is-user-author="isUserAuthor"
            :is-user-authentificated="isUserAuthentificated"
        ></author-bar>
        <div class="grid-item-bar">
            <div class="row">
                <div class="col-9">
                    <!-- TODO: Modal and Socket need a rewrite to get rid of grid-item-open-action -->
                    <span
                        v-if="edited"
                        class="grid-item-open-action"
                        :data-content-id="id"
                        :title="timestamp"
                    >
                        {{ humanizedTimestamp }}{{ editedText }}
                    </span> &nbsp;
                    <div v-if="isUserAuthor">
                        <a :href="updateUrl">
                            <i class="fa fa-pencil" title="Update" aria-label="Update"></i>
                        </a>
                        <a :href="deleteUrl">
                            <i class="fa fa-remove" title="Delete" aria-label="Delete"></i>
                        </a>
                    </div>
                </div>
                <div class="col-3 text-right grid-item-reactions mt-1">
                    <div v-if="showReactionBar" class="item-reaction">
                        <span class="item-open-replies-action" :data-content-id="id">
                            <i class="fa fa-envelope" title="Replies" aria-label="Replies"></i>
                        </span>
                        <span class="item-reaction-counter">{{ childrenCount }}</span>
                    </div>
                </div>
            </div>
        </div>
        <div v-if="showReactionBar" class="replies-container" :data-content-id="id">
            <div class="content-actions hidden" :data-content-id="id">
                <a class="btn btn-secondary" :href="replyUrl">Reply</a>
            </div>
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
            updateUrl: {type: String, required: true},
            deleteUrl: {type: String, required: true},
            replyUrl: {type: String, required: true},
            childrenCount: {type: Number, required: true},
            edited: {type: Boolean, required: true},
            isUserAuthor: {type: Boolean, required: true},
            showAuthorBar: {type: Boolean, required: true},
            isUserAuthentificated: {type: Boolean, required: true}
        },
        computed: {
            editedText() { return this.edited ? " (edited)" : "" },
            showReactionBar(){ return this.isUserAuthentificated || this.childrenCount > 0 }
        }
    });
</script>
