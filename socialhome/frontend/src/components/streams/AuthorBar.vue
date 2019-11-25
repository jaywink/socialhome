<template>
    <div>
        <div class="grid-item-author-bar mt-1">
            <div>
                <img :src="author.image_url_small" class="grid-item-author-bar-pic">
                <div class="author-bar-name-container">
                    <div class="profilebox-trigger" @click.stop.prevent="profileBoxTrigger">
                        {{ authorName }}
                    </div>
                    <div class="author-bar-timestamp">
                        <a :href="content.url" :title="content.timestamp" class="unstyled-link">
                            {{ timestampText }}
                        </a>
                        <i v-if="isLimited" class="fa fa-lock mr-2" aria-hidden="true" />
                    </div>
                    <div v-if="isShared">
                        <i class="fa fa-refresh mr-2 shared-icon" aria-hidden="true" />
                        <div class="profilebox-trigger" @click.stop.prevent="throughBoxTrigger">
                            {{ throughAuthorName }}
                        </div>
                        <div v-if="showThroughProfileBox" class="profile-box">
                            <div class="pull-right">
                                <profile-reaction-buttons
                                    :profile-uuid="content.through_author.uuid"
                                />
                            </div>
                            <div class="clearfix" />
                        </div>
                    </div>
                </div>
            </div>
            <div v-if="showProfileBox" class="profile-box">
                {{ authorFederationId }}
                <div class="pull-right">
                    <profile-reaction-buttons :profile-uuid="author.uuid" />
                </div>
                <div class="clearfix" />
            </div>
        </div>
    </div>
</template>

<script>
import ProfileReactionButtons from "@/components/common/ProfileReactionButtons.vue"


export default {
    components: {ProfileReactionButtons},
    props: {content: {type: Object, required: true}},
    data() {
        return {
            showProfileBox: false,
            showThroughProfileBox: false,
        }
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
        isUserAuthenticated() {
            return this.$store.state.application.isUserAuthenticated
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
        throughAuthorUrl() {
            return this.content.through_author.url || "#"
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
    methods: {
        profileBoxTrigger() {
            this.showProfileBox = !this.showProfileBox
        },
        throughBoxTrigger() {
            this.showThroughProfileBox = !this.showThroughProfileBox
        },
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
    .profilebox-trigger {
        cursor: pointer;
    }
</style>
