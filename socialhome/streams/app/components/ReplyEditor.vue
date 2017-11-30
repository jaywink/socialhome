<template>
    <div>
        <div class="mt-2">
            <b-form-textarea
                :max-rows="5"
                :placeholder="translations.replyText"
                :rows="5"
                v-model="replyText"
            ></b-form-textarea>
        </div>
        <div class="pull-right">
            <a :href="fullEditorUrl" target="_blank" rel="noopener noreferrer">{{ translations.fullEditor }}</a>
        </div>
        <div class="reply-save-button">
            <b-button @click.prevent.stop="saveReply" variant="primary">{{ translations.save }}</b-button>
        </div>
    </div>
</template>


<script>
import Vue from "vue"

import {streamStoreOperations} from "streams/app/stores/streamStore.operations";


export default Vue.component("reply-editor", {
    props: {
        contentId: {type: Number, required: true},
    },
    data() {
        return {
            replyText: "",
        }
    },
    computed: {
        fullEditorUrl() {
            return Urls["content:reply"]({pk: this.contentId})
        },
        translations() {
            return {
                fullEditor: gettext("Full editor"),
                replyText: gettext("Reply text..."),
                save: gettext("Save"),
            }
        },
    },
    methods: {
        saveReply() {
            this.$store.dispatch(
                streamStoreOperations.saveReply, {
                    data: {parent: this.contentId, text: this.replyText},
                }
            )
            this.replyText = ""
        },
    },
})
</script>


<style scoped lang="scss">
    .reply-save-button {
        padding-top: 10px;

        a, button {
            width: 100%;
            cursor: pointer;
        }
    }
</style>
