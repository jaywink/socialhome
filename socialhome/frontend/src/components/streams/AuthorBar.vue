<template>
    <div>
        <div class="grid-item-author-bar mt-1">
            <div class="profilebox-trigger" @click.stop.prevent="profileBoxTrigger">
                <img :src="author.image_url_small" class="grid-item-author-bar-pic">
                {{ authorName }}
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
        isUserAuthenticated() {
            return this.$store.state.application.isUserAuthenticated
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
    .profilebox-trigger {
        cursor: pointer;
    }
</style>
