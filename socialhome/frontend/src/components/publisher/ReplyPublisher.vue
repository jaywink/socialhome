<template>
    <div class="socialhome-publisher">
        <h1>{{ titleText }}</h1>

        <markdown-editor v-model="baseModel.text" />

        <b-form @submit.stop.prevent="onPostForm">
            <b-row>
                <b-col>
                    <b-form-group label-for="show-preview">
                        <template slot="label">
                            {{ translations.showPreview }}<br>
                            <b-form-checkbox
                                id="show-preview"
                                v-model="baseModel.showPreview"
                                name="show_preview"
                            />
                            <b-form-text>
                                {{ translations.showPreviewHelp }}
                            </b-form-text>
                        </template>
                    </b-form-group>
                </b-col>
            </b-row>
            <b-button
                class="w-100 pointer"
                type="submit"
                variant="primary"
            >
                {{ "Save" | gettext }}
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
    computed: {
        titleText() {
            return this.translations.reply
        },
    },
    methods: {
        onPostForm() {
            this.$store.dispatch("publisher/publishReply", {
                ...this.model, parent: this.parentId,
            })
                .then(url => window.location.replace(url))
                .catch(() => this.$snotify.error(this.translations.postUploadError, {timeout: 10000}))
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
