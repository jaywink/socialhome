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
                </div>
            </div>
            <div v-show="showProfileBox" class="profile-box">
                {{ authorFederationId }}
                <div class="pull-right">
                    <profile-reaction-buttons :profile="author" :user-following="content.user_following_author" />
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
        return {showProfileBox: false}
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
        isUserAuthenticated() {
            return this.$store.state.application.isUserAuthenticated
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
    },
}
</script>

<style scoped lang="scss">
    .author-bar-name-container {
        display: inline-block;
        vertical-align: middle;
    }
    .author-bar-timestamp {
        color: #B39A96;
    }
    .profilebox-trigger {
        cursor: pointer;
    }
</style>
