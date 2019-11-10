<!-- eslint-disable max-len -->
<template>
    <div class="socialhome-publisher">
        <h1>{{ titleText }}</h1>

        <markdown-editor v-model="model.text" />

        <b-form @submit.stop.prevent="onPostForm">
            <b-row>
                <b-col v-if="!isReply">
                    <b-form-group
                        v-show="model.visibility === visibilityOptions.LIMITED.value"
                        :label="translations.recipients"
                        label-for="recipients"
                    >
                        <b-form-input
                            id="recipients"
                            v-model="model.recipients"
                            name="recipients"
                        />
                        <b-form-invalid-feedback :state="errors.recipientsErrors.length > 0">
                            {{ errors.recipientsErrors }}
                        </b-form-invalid-feedback>
                        <template slot="label">
                            {{ "Type in the handles (eg user@example.com) of the recipients. Separate by commas. Sorry, no search yet.." | gettext }}
                        </template>
                    </b-form-group>

                    <b-form-group
                        v-show="model.visibility === visibilityOptions.LIMITED.value"
                        label-for="include-following"
                    >
                        <template slot="label">
                            {{ translations.includeFollowing }}<br>
                            <b-form-checkbox
                                id="include-following"
                                v-model="model.includeFollowing"
                                name="include_following"
                            />
                            <b-form-text>
                                {{ "Automatically includes all the people you follow as recipients." | gettext }}
                            </b-form-text>
                        </template>
                    </b-form-group>

                    <b-form-group
                        :label="translations.visibility"
                        label-for="visibility"
                    >
                        <b-form-select
                            id="visibility"
                            v-model="model.visibility"
                            name="visibility"
                            :selected="visibilityOptions.PUBLIC.value"
                            :options="Object.values(visibilityOptions)"
                        />
                        <b-form-text>
                            <ul>
                                <li>{{ "Public - visible to anyone, even anonymous users and internet search bots." | gettext }}</li>
                                <li>{{ "Limited - visible to only those who shared with." | gettext }}</li>
                                <li>{{ "Site - visible to only users who are logged in. Does not federate to other servers." | gettext }}</li>
                                <li>{{ "Self - visible to only self. Does not federate to other servers." | gettext }}</li>
                            </ul>
                            <p>{{ "Tip: You can use the 'Self' visibility to create draft content and then change the visibility to for example 'Public' when you want to publish it." | gettext }}</p>
                        </b-form-text>
                    </b-form-group>
                </b-col>

                <b-col>
                    <template v-if="!isReply">
                        <b-form-group label-for="pinned">
                            <template slot="label">
                                {{ translations.pinned }}<br>
                                <b-form-checkbox
                                    id="pinned"
                                    v-model="model.pinned"
                                    name="pinned"
                                />
                                <b-form-text>
                                    {{ "Pinned content will be shown on your personal profile in the order you want. Reorder pinned content from the profile menu. Pinned content will federate and otherwise function as any other content." | gettext }}
                                </b-form-text>
                            </template>
                        </b-form-group>

                        <b-form-group label-for="federate">
                            <template slot="label">
                                {{ translations.federate }}<br>
                                <b-form-checkbox
                                    id="federate"
                                    v-model="model.federate"
                                    name="federate"
                                />
                                <b-form-text>
                                    {{ "Disable to skip federating this version to remote servers. Note, saved content version will still be updated to local streams." | gettext }}
                                </b-form-text>
                            </template>
                        </b-form-group>
                    </template>

                    <b-form-group label-for="show-preview">
                        <template slot="label">
                            {{ translations.showPreview }}<br>
                            <b-form-checkbox
                                id="show-preview"
                                v-model="model.showPreview"
                                name="show_preview"
                            />
                            <b-form-text>
                                {{ "Disable to turn off fetching and showing an OEmbed or OpenGraph preview using the links in the text." | gettext }}
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
<!-- eslint-enable max-len -->

<script>
import _get from "lodash/get"
import MarkdownEditor from "@/components/publisher/MarkdownEditor"

const VISIBILITY_OPTIONS = Object.freeze({
    PUBLIC: {value: 0, text: gettext("Public")},
    LIMITED: {value: 1, text: gettext("Limited (not supported yet)"), disabled: true},
    SITE: {value: 2, text: gettext("Site")},
    SELF: {value: 3, text: gettext("Self")},
})

export default {
    name: "Publisher",
    components: {MarkdownEditor},
    props: {contentId: {type: String, default: null}},
    data() {
        return {
            model: {
                federate: true,
                includeFollowing: false,
                pinned: false,
                recipients: "",
                showPreview: true,
                text: "",
                visibility: VISIBILITY_OPTIONS.PUBLIC.value,
            },
            errors: {recipientsErrors: ""},
        }
    },
    computed: {
        isReply() {
            return _get(window, ["context", "isReply"], undefined)
        },
        titleText() {
            if (this.isReply) {
                if (this.contentId) {
                    return this.translations.updateReply
                }
                return this.translations.reply
            } if (this.contentId) {
                return this.translations.reply
            }

            return this.translations.create
        },
        translations() {
            return {
                create: gettext("Create"),
                federate: gettext("Federate to remote servers"),
                hiddenTextarea: gettext("Hidden textarea"),
                includeFollowing: gettext("Include people I follow"),
                recipients: gettext("Recipients"),
                reply: gettext("Reply"),
                updateReply: gettext("Update reply"),
                visibility: gettext("Visibility"),
                pinned: gettext("Pinned to profile"),
                postUploadError: gettext("Error saving content."),
                showPreview: gettext("Show OEmbed or OpenGraph preview"),
            }
        },
        visibilityOptions() { return VISIBILITY_OPTIONS },
    },
    methods: {
        onPostForm() {
            this.$store.dispatch("publisher/publishPost", {...this.model, parent: this.contentId})
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
