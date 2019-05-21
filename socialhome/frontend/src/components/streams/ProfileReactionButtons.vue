<template>
  <div>
    <b-button
      v-if="showProfileLink"
      :href="profile.url"
      variant="secondary"
      :title="translations.profile"
      :aria-label="translations.profile"
    >
      <i class="fa fa-user" />
    </b-button>
    <b-button
      v-if="!profile.is_local"
      :href="profile.home_url"
      variant="secondary"
      :title="translations.home"
      :aria-label="translations.home"
    >
      <i class="fa fa-home" />
    </b-button>
    <b-button
      v-if="showUnfollowBtn"
      variant="secondary"
      class="unfollow-btn"
      :title="translations.unfollow"
      :aria-label="translations.unfollow"
      @click.prevent.stop="unfollow"
    >
      <i class="fa fa-minus" />
    </b-button>
    <b-button
      v-if="showFollowBtn"
      variant="secondary"
      class="follow-btn"
      :title="translations.follow"
      :aria-label="translations.follow"
      @click.prevent.stop="follow"
    >
      <i class="fa fa-plus" />
    </b-button>
  </div>
</template>

<script>
export default {
    name: "ProfileReactionButtons",
    props: {
        userFollowing: {type: Boolean, default: false},
        profile: {type: Object, required: true},
        showProfileLink: {type: Boolean, default: true},
    },
    data() {
        return {following: this.userFollowing}
    },
    computed: {
        currentBrowsingProfileId() {
            return this.$store.state.application.currentBrowsingProfileId
        },
        displayName() {
            return this.profile.name ? this.profile.name : this.profile.fid
        },
        isUserAuthenticated() {
            return this.$store.state.application.isUserAuthenticated
        },
        showFollowBtn() {
            return this.$store.state.application.isUserAuthenticated && !this.following
        },
        showUnfollowBtn() {
            return this.$store.state.application.isUserAuthenticated && this.following
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
                followUrl: Urls["api:profile-follow"]({uuid: this.profile.uuid}),
                unfollowUrl: Urls["api:profile-unfollow"]({uuid: this.profile.uuid}),
            }
        },
    },
    methods: {
        follow() {
            if (!this.isUserAuthenticated) {
                this.$snotify.error(gettext("You must be logged in to follow someone"))
                return
            }
            this.$http.post(this.urls.followUrl)
                .then(() => this.following = true)
                .catch(() => this.$snotify.error(
                    `${gettext("An error happened while trying to follow")} ${this.displayName}`,
                ))
        },
        unfollow() {
            if (!this.isUserAuthenticated) {
                this.$snotify.error(gettext("You must be logged in to unfollow someone"))
                return
            }
            this.$http.post(this.urls.unfollowUrl)
                .then(() => this.following = false)
                .catch(() => this.$snotify.error(
                    `${gettext("An error happened while trying to unfollow")} ${this.displayName}`,
                ))
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
