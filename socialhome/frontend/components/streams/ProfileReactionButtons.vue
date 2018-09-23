<template>
    <div>
        <b-button
            v-if="showProfileLink"
            :href="profile.url"
            variant="secondary"
            :title="translations.profile"
            :aria-label="translations.profile"
        >
            <i class="fa fa-user"></i>
        </b-button>
        <b-button
            v-if="!profile.is_local"
            :href="profile.home_url"
            variant="secondary"
            :title="translations.home"
            :aria-label="translations.home"
        >
            <i class="fa fa-home"></i>
        </b-button>
        <b-button
            @click.prevent.stop="unfollow"
            variant="secondary"
            v-if="showUnfollowBtn"
            class="unfollow-btn"
            :title="translations.unfollow"
            :aria-label="translations.unfollow"
        >
            <i class="fa fa-minus"></i>
        </b-button>
        <b-button
            @click.prevent.stop="follow"
            variant="secondary"
            v-if="showFollowBtn"
            class="follow-btn"
            :title="translations.follow"
            :aria-label="translations.follow"
        >
            <i class="fa fa-plus"></i>
        </b-button>
    </div>
</template>

<script>


export default {
    name: "profile-reaction-buttons",
    data() {
        return {
            following: this.userFollowing,
        }
    },
    props: {
        userFollowing: {type: Boolean, default: false},
        profile: {type: Object, required: true},
        showProfileLink: {type: Boolean, default: true},
    },
    computed: {
        currentBrowsingProfileId() {
            return this.$store.state.applicationStore.currentBrowsingProfileId
        },
        displayName() {
            return this.profile.name ? this.profile.name : this.profile.fid
        },
        isUserAuthenticated() {
            return this.$store.state.applicationStore.isUserAuthenticated
        },
        showFollowBtn() {
            return this.$store.state.applicationStore.isUserAuthenticated && !this.following
        },
        showUnfollowBtn() {
            return this.$store.state.applicationStore.isUserAuthenticated && this.following
        },
        translations() {
            return {
                follow: gettext("Follow"),
                home: gettext("Home"),
                profile: gettext("Profile"),
                unfollow: gettext("Unfollow"),
            }
        },
        urls() {
            return {
                followUrl: Urls["api:profile-add-follower"]({pk: this.currentBrowsingProfileId}),
                unfollowUrl: Urls["api:profile-remove-follower"]({pk: this.currentBrowsingProfileId}),
            }
        },
    },
    methods: {
        follow() {
            if (!this.isUserAuthenticated) {
                this.$snotify.error(gettext("You must be logged in to follow someone"))
                return
            }
            this.$http.post(this.urls.followUrl, {uuid: this.profile.uuid})
                .then(() => this.following = true)
                .catch(_ => this.$snotify.error(
                    `${gettext("An error happened while trying to follow")} ${this.displayName}`))
        },
        unfollow() {
            if (!this.isUserAuthenticated) {
                this.$snotify.error(gettext("You must be logged in to unfollow someone"))
                return
            }
            this.$http.post(this.urls.unfollowUrl, {uuid: this.profile.uuid})
                .then(() => this.following = false)
                .catch(_ => this.$snotify.error(
                    `${gettext("An error happened while trying to unfollow")} ${this.displayName}`))
        },
    },
}
</script>

<style scoped lang="scss">
    .follow-btn,
    .unfollow-btn {
        cursor: pointer;
    }
</style>
