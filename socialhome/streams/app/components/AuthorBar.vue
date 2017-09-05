<template>
    <div>
        <div class="grid-item-author-bar mt-1">
            <div @click.stop.prevent="profileBoxTrigger" class="profilebox-trigger">
                <img :src="author.image_url_small" class="grid-item-author-bar-pic" />
                {{ author.name.length ? author.name : author.handle }}
            </div>
            <div v-show="showProfileBox" class="profile-box">
                {{ author.handle }}
                <div class="pull-right">
                    <b-button :href="author.absolute_url" variant="secondary" title="Profile" aria-label="Profile">
                        <i class="fa fa-user"></i>
                    </b-button>
                    <b-button
                        v-if="isUserRemote"
                        :href="author.home_url"
                        variant="secondary"
                        title="Home"
                        aria-label="Home"
                    >
                        <i class="fa fa-home"></i>
                    </b-button>
                    <b-button
                        @click.prevent.stop="unfollow"
                        variant="secondary"
                        v-if="showUnfollowBtn"
                        class="unfollow-btn"
                        title="Unfollow"
                        aria-label="Unfollow"
                    >
                        <i class="fa fa-minus"></i>
                    </b-button>
                    <b-button
                        @click.prevent.stop="follow"
                        variant="secondary"
                        v-if="showFollowBtn"
                        class="follow-btn"
                        title="Follow"
                        aria-label="Follow"
                    >
                        <i class="fa fa-plus"></i>
                    </b-button>
                </div>
                <div class="clearfix"></div>
            </div>
        </div>
    </div>
</template>

<script>
import Vue from "vue"


export default Vue.component("author-bar", {
    props: {
        contentId: {type: Number, required: true},
    },
    data() {
        return {
            showProfileBox: false,
        }
    },
    computed: {
        author() {
            return this.$store.state.contents[this.contentId].author
        },
        canFollow() {
            return this.$store.state.applicationStore.isUserAuthenticated
                && !this.$store.state.contents[this.contentId].user_is_author
        },
        currentBrowsingProfileId() {
            return this.$store.state.applicationStore.currentBrowsingProfileId
        },
        isUserAuthenticated() {
            return this.$store.state.applicationStore.isUserAuthenticated
        },
        isUserFollowingAuthor: {
            get: function () {
                return this.$store.state.contents[this.contentId].user_following_author
            },
            set: function (value) {
                this.$store.state.contents[this.contentId].user_following_author = value
            },
        },
        isUserRemote() {
            return !this.$store.state.contents[this.contentId].local
        },
        showFollowBtn() {
            return this.canFollow && !this.isUserFollowingAuthor
        },
        showUnfollowBtn() {
            return this.canFollow && this.isUserFollowingAuthor
        },
    },
    methods: {
        profileBoxTrigger() {
            this.showProfileBox = !this.showProfileBox
        },
        unfollow() {
            if (!this.isUserAuthenticated) {
                console.error("Not logged in")
                return
            }
            this.$http.post(`/api/profiles/${this.currentBrowsingProfileId}/remove_follower/`, {guid: this.author.guid})
                .then(() => this.isUserFollowingAuthor = false)
                .catch(err => console.error(err) /* TODO: Proper error handling */)
        },
        follow() {
            if (!this.isUserAuthenticated) {
                console.error("Not logged in")
                return
            }
            this.$http.post(`/api/profiles/${this.currentBrowsingProfileId}/add_follower/`, {guid: this.author.guid})
                .then(() => this.isUserFollowingAuthor = true)
                .catch(err => console.error(err) /* TODO: Proper error handling */)
        },
    },
    updated() {
        Vue.redrawVueMasonry()
    },
})
</script>

<style scoped lang="scss">
    .profilebox-trigger,
    .follow-btn,
    .unfollow-btn {
        cursor: pointer;
    }
</style>
