<template>
    <div>
        <div class="mt-2">
            <b-form-textarea
                v-model="replyText"
                :max-rows="5"
                :placeholder="translations.replyText"
                :rows="5"
                autofocus
            />
        </div>
        <div class="pull-right">
            <a :href="fullEditorUrl" target="_blank" rel="noopener noreferrer">{{ translations.fullEditor }}</a>
        </div>
        <div
            class="reply-save-button"
        >
            <b-button variant="primary" @click.prevent.stop="saveReply">
                {{ translations.replySave }}
            </b-button>
        </div>
    </div>
</template>

<script>
import Vue from "vue"

export default Vue.component("ReplyEditor", {
    props: {
        contentId: {
            type: Number, required: true,
        },
        contentVisibility: {
            type: String, required: true,
        },
        prefilledText: {
            type: String, required: false, default: "",
        },
        toggleReplyEditor: {
            type: Function, default: () => {},
        },
    },
    data() {
        return {replyText: this.prefilledText}
    },
    computed: {
        fullEditorUrl() {
            return Urls["content:reply"]({pk: this.contentId})
        },
        translations() {
            return {
                fullEditor: gettext("Full editor"),
                replySave: gettext("Reply"),
                replyText: gettext("Reply text..."),
            }
        },
    },
    methods: {
        saveReply() {
            if (this.replyText) {
                const re = /@([\w\-.]+@[\w\-.]+\.[A-Za-z0-9]+)[\W\s]?/g
                const recipients = Array.from(this.replyText.matchAll(re), m => m[1])
                this.$store.dispatch(
                    "stream/saveReply", {
                        data: {
                            parent: this.contentId,
                            text: this.replyText,
                            recipients,
                        },
                    },
                )
                this.replyText = ""
                this.toggleReplyEditor()
            }
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
