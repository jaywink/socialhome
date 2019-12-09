<template>
    <div>
        <div class="grid-item-author-bar mt-1">
            <div>
                <img :src="author.image_url_small" class="grid-item-author-bar-pic">
                <div class="author-bar-name-container">
                    <popper
                        trigger="clickToToggle"
                        :options="{
                            placement: 'bottom-start'
                        }"
                    >
                        <div class="popper">
                            {{ authorFederationId }}
                            <profile-reaction-buttons :profile-uuid="author.uuid" />
                        </div>
                        <div slot="reference" class="pointer">
                            {{ authorName }}
                        </div>
                    </popper>
                    <div class="author-bar-timestamp">
                        <a :href="content.url" :title="content.timestamp" class="unstyled-link">
                            {{ timestampText }}
                        </a>
                        <i v-if="isLimited" class="fa fa-lock mr-2" aria-hidden="true" />
                    </div>
                    <div v-if="isShared">
                        <popper
                            trigger="clickToToggle"
                            :options="{
                                placement: 'bottom-start'
                            }"
                        >
                            <div class="popper">
                                {{ throughAuthorFederationId }}
                                <profile-reaction-buttons
                                    :profile-uuid="content.through_author.uuid"
                                />
                            </div>
                            <div slot="reference" class="pointer">
                                <i class="fa fa-refresh mr-2 shared-icon" aria-hidden="true" /> {{ throughAuthorName }}
                            </div>
                        </popper>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Popper from "vue-popperjs"
import "vue-popperjs/dist/vue-popper.css"
import ProfileReactionButtons from "@/components/common/ProfileReactionButtons.vue"

export default {
    components: {
        Popper, ProfileReactionButtons,
    },
    props: {
        content: {
            type: Object, required: true,
        },
    },
    computed: {
        author() {
            return this.content.author
        },
        authorFederationId() {
            if (this.author.handle) {
                return this.author.handle
            }
            return this.author.fid
        },
        authorName() {
            if (this.author.name) {
                return this.author.name
            } if (this.author.handle) {
                return this.author.handle
            }
            return this.author.fid
        },
        isLimited() {
            return this.content.visibility === "limited"
        },
        isShared() {
            return this.content.through !== this.content.id
        },
        throughAuthorFederationId() {
            const throughAuthor = this.content.through_author
            if (throughAuthor.handle) {
                return throughAuthor.handle
            }
            return throughAuthor.fid
        },
        throughAuthorName() {
            const throughAuthor = this.content.through_author
            if (throughAuthor.name) {
                return throughAuthor.name
            } if (throughAuthor.handle) {
                return throughAuthor.handle
            }
            return throughAuthor.fid || ""
        },
        timestampText() {
            return this.content.edited
                ? `${this.content.humanized_timestamp} (${gettext("edited")})`
                : this.content.humanized_timestamp
        },
    },
    updated() {
        this.$redrawVueMasonry()
    },
}
</script>

<style scoped lang="scss">
    .author-bar-name-container {
        display: inline-block;
        vertical-align: middle;
    }
    .author-bar-timestamp, .shared-icon {
        color: #B39A96;
    }
</style>
