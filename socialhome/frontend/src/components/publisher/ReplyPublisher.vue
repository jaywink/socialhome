<template>
    <div class="socialhome-publisher">
        <h1>{{ titleText }}</h1>

        <markdown-editor ref="editor" v-model="baseModel.text" @input="extractMentions" />

        <b-form @submit.stop.prevent="onPostForm">
            <b-row>
                <b-col>
                    <b-form-group label-for="show-preview">
                        <template slot="label">
                            <b-form-checkbox
                                id="show-preview"
                                v-model="baseModel.showPreview"
                                name="show_preview"
                                switch
                            >
                                {{ translations.showPreview }}
                            </b-form-checkbox>
                            <b-form-text>
                                {{ translations.showPreviewHelp }}
                            </b-form-text>
                        </template>
                    </b-form-group>
                </b-col>
            </b-row>
            <b-button
                class="socialhome-publisher-submit-btn w-100 pointer"
                type="submit"
                variant="primary"
                :disabled="isPosting"
            >
                <div v-show="!isPosting">
                    {{ "Save" | gettext }}
                </div>
                <simple-loading-element v-show="isPosting" />
            </b-button>
        </b-form>
    </div>
</template>

<script>
import publisherMixin from "@/components/publisher/publisher-mixin"

export default {
    name: "ReplyPublisher",
    mixins: [publisherMixin],
    props: {
        parentId: {
            type: String, required: true,
        },
    },
    data() {
        return {extendedModel: {recipients: []}}
    },
    computed: {
        titleText() {
            return this.translations.reply
        },
    },
    methods: {
        postFormRequest() {
            const payload = {
                ...this.model,
                parent: this.parentId,
            }
            return this.$store.dispatch("publisher/publishReply", payload)
        },
    },
}
</script>

<style lang="scss">
    .socialhome-publisher {
        .text-muted {
            color: white !important; // Overrides BS' defaults
        }
    }
</style>
