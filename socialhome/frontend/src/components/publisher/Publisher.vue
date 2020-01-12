<template>
    <div class="socialhome-publisher">
        <h1>{{ titleText }}</h1>

        <markdown-editor v-model="baseModel.text" />

        <b-form @submit.stop.prevent="onPostForm">
            <b-row>
                <b-col>
                    <b-form-group
                        :label="translations.visibility"
                        label-for="visibility"
                    >
                        <b-form-select
                            id="visibility"
                            v-model="extendedModel.visibility"
                            name="visibility"
                            :selected="visibilityOptions.PUBLIC.value"
                            :options="Object.values(visibilityOptions)"
                        />
                        <b-form-text>
                            <ul>
                                <li v-for="v in visibilityOptions" :key="v.value">
                                    {{ v.text + " — " + v.help }}
                                </li>
                            </ul>
                            <p>{{ translations.visibilityHelp }}</p>
                        </b-form-text>
                    </b-form-group>

                    <b-form-group
                        v-show="extendedModel.visibility === visibilityOptions.LIMITED.value"
                        :label="translations.recipients"
                        label-for="recipients"
                    >
                        <b-form-input
                            id="recipients"
                            v-model="extendedModel.recipients"
                            name="recipients"
                        />
                        <b-form-invalid-feedback :state="errors.recipientsErrors.length > 0">
                            {{ errors.recipientsErrors }}
                        </b-form-invalid-feedback>
                        <template slot="label">
                            {{ translations.recipientsHelp }}
                        </template>
                    </b-form-group>

                    <b-form-group
                        v-show="extendedModel.visibility === visibilityOptions.LIMITED.value"
                        label-for="include-following"
                    >
                        <template slot="label">
                            {{ translations.includeFollowing }}<br>
                            <b-form-checkbox
                                id="include-following"
                                v-model="extendedModel.includeFollowing"
                                name="include_following"
                            />
                            <b-form-text>
                                {{ "Automatically includes all the people you follow as recipients." | gettext }}
                            </b-form-text>
                        </template>
                    </b-form-group>
                </b-col>

                <b-col>
                    <b-form-group label-for="pinned">
                        <template slot="label">
                            {{ translations.pinned }}<br>
                            <b-form-checkbox
                                id="pinned"
                                v-model="extendedModel.pinned"
                                name="pinned"
                            />
                            <b-form-text>
                                {{ translations.pinnedHelp }}
                            </b-form-text>
                        </template>
                    </b-form-group>

                    <b-form-group label-for="federate">
                        <template slot="label">
                            {{ translations.federate }}<br>
                            <b-form-checkbox
                                id="federate"
                                v-model="extendedModel.federate"
                                name="federate"
                            />
                            <b-form-text>
                                {{ translations.federateHelp }}
                            </b-form-text>
                        </template>
                    </b-form-group>

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
import publisherMixin, {VISIBILITY_OPTIONS} from "@/components/publisher/publisher-mixin"


export default {
    name: "Publisher",
    mixins: [publisherMixin],
    data() {
        return {
            extendedModel: {
                federate: true,
                includeFollowing: false,
                pinned: false,
                recipients: "",
                visibility: VISIBILITY_OPTIONS.PUBLIC.value,
            },
        }
    },
    computed: {
        titleText() {
            return this.translations.create
        },
    },
    methods: {
        postFormRequest() {
            return this.$store.dispatch("publisher/publishPost", this.model)
        },
    },
}
</script>

<style lang="scss">
    .socialhome-publisher {
        .text-muted {
            color: white !important; // Overrides BS' defaults
        }
        .socialhome-publisher-submit-btn {
            &:disabled, &.disabled {
                cursor: wait !important; // Overrides BS' defaults
            }
        }
    }
</style>
