<template>
    <div class="socialhome-publisher">
        <h1>{{ titleText }}</h1>

        <markdown-editor ref="editor" v-model="baseModel.text" @input="extractMentions" />

        <b-form :validated="wasValidated" @submit.stop.prevent="onPostForm">
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

                    <b-form-group v-show="extendedModel.visibility === visibilityOptions.LIMITED.value">
                        <p>{{ translations.recipientsHelp }}</p>
                        <b-form-invalid-feedback :state="errors.recipientsErrors.length > 0">
                            {{ errors.recipientsErrors }}
                        </b-form-invalid-feedback>
                        <b-form-checkbox-group
                            ref="includeFollowing"
                            v-model="includeFollowingAccessor"
                            :state="includeFollowingFormControlState"
                            :options="[{text: translations.includeFollowing, value: true, name: 'include_following' }]"
                            switches
                        >
                            <b-form-invalid-feedback :state="includeFollowingFormControlState">
                                {{ errors.includeFollowingErrors }}
                            </b-form-invalid-feedback>
                        </b-form-checkbox-group>
                        <b-form-text>
                            {{ translations.includeFollowingHelp }}
                        </b-form-text>
                    </b-form-group>
                </b-col>

                <b-col>
                    <b-form-group label-for="pinned">
                        <template slot="label">
                            <b-form-checkbox
                                id="pinned"
                                v-model="extendedModel.pinned"
                                name="pinned"
                                switch
                            >
                                {{ translations.pinned }}
                            </b-form-checkbox>
                            <b-form-text>
                                {{ translations.pinnedHelp }}
                            </b-form-text>
                        </template>
                    </b-form-group>

                    <b-form-group label-for="federate">
                        <template slot="label">
                            <br>
                            <b-form-checkbox
                                id="federate"
                                v-model="extendedModel.federate"
                                name="federate"
                                switch
                            >
                                {{ translations.federate }}
                            </b-form-checkbox>
                            <b-form-text>
                                {{ translations.federateHelp }}
                            </b-form-text>
                        </template>
                    </b-form-group>

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
import _difference from "lodash/difference"

import publisherMixin, {VISIBILITY_OPTIONS} from "@/components/publisher/publisher-mixin"
import bookmarkletMixin from "@/components/publisher/bookmarklet-mixin"

const ERRORS = Object.freeze({
    FOLLOWING_AND_RECIPIENTS: "FOLLOWING_AND_RECIPIENTS",
    RECIPIENTS_NOT_FOUND: "RECIPIENTS_NOT_FOUND",
    NONE: "NONE",
})

export default {
    name: "Publisher",
    mixins: [publisherMixin, bookmarkletMixin],
    data() {
        return {
            extendedModel: {
                federate: true,
                includeFollowing: false,
                pinned: false,
                recipients: [],
                visibility: VISIBILITY_OPTIONS.PUBLIC.value,
            },
        }
    },
    computed: {
        hasErrors() {
            if (this.followingAndRecipientsError) {
                return ERRORS.FOLLOWING_AND_RECIPIENTS
            } if (this.recipientsNotFoundError) {
                return ERRORS.RECIPIENTS_NOT_FOUND
            }
            return ERRORS.NONE
        },
        includeFollowingAccessor: {
            get() {
                return this.extendedModel.includeFollowing ? [true] : []
            },
            set(value) {
                this.extendedModel.includeFollowing = (value.length !== 0)
            },
        },
        includeFollowingFormControlState() {
            if (!this.wasValidated) return null
            return this.errors.includeFollowingErrors.length <= 0
        },
        followingAndRecipientsError() {
            return this.extendedModel.visibility === VISIBILITY_OPTIONS.LIMITED.value
                && this.extendedModel.includeFollowing !== true
                && this.extendedModel.recipients.length === 0
        },
        recipientsNotFoundError() {
            if (this.followingAndRecipientsError) {
                return false
            }

            /*
             * `this.errors.recipientsNotFoundErrors` contains the list of recipients that are unknown
             * to the server.
             *
             * We compute which elements of `this.errors.recipientsNotFoundErrors` which are not
             * present in `this.extendedModel.recipients`. If every element of `this.errors.recipientsNotFoundErrors`
             * are absent from `this.extendedModel.recipients` that difference and
             * `this.errors.recipientsNotFoundErrors` should have equal size.
             */
            const recipientInError = _difference(this.errors.recipientsNotFoundErrors, this.extendedModel.recipients)
            // Will be true if recipients list contains recipients that couldn't be found by the server
            return this.extendedModel.recipients !== 0
                && recipientInError.length < this.errors.recipientsNotFoundErrors.length
        },
        recipientsFormControlState() {
            if (!this.wasValidated) return null
            return this.errors.recipientsErrors.length <= 0
        },
        recipientsText: {
            get() {
                return this.extendedModel.recipients.join(",")
            },
            set(value) {
                this.extendedModel.recipients = value.split(",")
                    .map(it => it.trim())
                    .filter(it => it.length > 0)
            },
        },
        titleText() {
            return this.translations.create
        },
    },
    beforeMount() {
        /*
         * This is tricky: we don't want to show validation errors before
         * the user tried to submit the form for the first time. So we need
         * to start computing errors after that moment.
         */
        const unwatch = this.$watch("wasValidated", (newVal, oldVal) => {
            if (oldVal === null && newVal != null) {
                unwatch()
                this.$watch(
                    "hasErrors",
                    this.hasErrorsCallback,
                    {immediate: true},
                )
            }
        })
    },
    methods: {
        handleRequestErrors(code, message, payload = {}) {
            if (code === "recipients_not_found_error") {
                const html = `<div class="socialhome-publisher-recipients-error-message">
                                ${message}
                                <ul>
                                  <li>${payload.join("</li><li>")}</li>
                                </ul>
                              </div>`
                this.$snotify.error("", {
                    timeout: 0, html,
                })
                this.errors.recipientsNotFoundErrors.length = 0
                this.errors.recipientsNotFoundErrors.push(...payload)
                this.wasValidated = true
            }
        },
        // eslint-disable-next-line no-unused-vars
        hasErrorsCallback(newVal, _) {
            // Reset the errors
            this.errors.recipientsErrors = ""
            this.errors.includeFollowingErrors = ""

            if (newVal === ERRORS.FOLLOWING_AND_RECIPIENTS) {
                this.wasValidated = true
                this.errors.recipientsErrors = this.translations.limitedVisibilityError
                this.errors.includeFollowingErrors = this.translations.limitedVisibilityError
            } else if (newVal === ERRORS.RECIPIENTS_NOT_FOUND) {
                this.wasValidated = true
                this.errors.recipientsErrors = this.translations.recipientsNotFoundError
            }

            this.setRecipientsCustomValidity()
            this.setIncludeFollowingCustomValidity()
        },
        checkErrors() {
            let hasErrors = false
            if (this.followingAndRecipientsError || this.recipientsNotFoundError) {
                this.wasValidated = true
                hasErrors = true
            }

            return hasErrors
        },
        postFormRequest() {
            if (this.checkErrors()) return Promise.reject(Error(this.translations.validationError))
            return this.$store.dispatch("publisher/publishPost", this.model)
        },
        setRecipientsCustomValidity() {
            this.$refs.recipients.$el.setCustomValidity(this.errors.recipientsErrors)
        },
        setIncludeFollowingCustomValidity() {
            this.$refs.includeFollowing.$el.querySelector("input")
                .setCustomValidity(this.errors.includeFollowingErrors)
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

    .socialhome-publisher-recipients-error-message {
        &, & * {
            color: white;
        }

        & ul {
            max-height: 10rem;
            overflow-y: scroll;
        }
    }
</style>
