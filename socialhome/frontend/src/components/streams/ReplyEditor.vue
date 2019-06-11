<template>
  <div>
    <div class="mt-2">
      <b-form-textarea
        v-model="replyText"
        :max-rows="5"
        :placeholder="translations.replyText"
        :rows="5"
      />
    </div>
    <div class="pull-right">
      <a :href="fullEditorUrl" target="_blank" rel="noopener noreferrer">{{ translations.fullEditor }}</a>
    </div>
    <div class="reply-save-button">
      <b-button variant="primary" @click.prevent.stop="saveReply">
        {{ translations.save }}
      </b-button>
    </div>
  </div>
</template>


<script>
import Vue from "vue"

export default Vue.component("reply-editor", {
    props: {contentId: {type: Number, required: true}},
    data() {
        return {replyText: ""}
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
            if (this.replyText) {
                this.$store.dispatch(
                    "stream/saveReply", {data: {parent: this.contentId, text: this.replyText}},
                )
                this.replyText = ""
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
