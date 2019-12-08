<template>
    <div v-if="profile" class="socialhome-profile-reaction-buttons">
        <b-button
            v-if="showProfileLink"
            :href="profile.url"
            variant="outline-dark"
            :title="translations.profile"
            :aria-label="translations.profile"
        >
            <i class="fa fa-user" />
        </b-button>
        <b-button
            v-if="!profile.is_local"
            :href="profile.home_url"
            variant="outline-dark"
            :title="translations.home"
            :aria-label="translations.home"
        >
            <i class="fa fa-home" />
        </b-button>
        <b-button
            v-if="showUnfollowBtn"
            variant="outline-dark"
            class="unfollow-btn"
            :title="translations.unfollow"
            :aria-label="translations.unfollow"
            @click.prevent.stop="unfollow"
        >
            <i class="fa fa-minus" />
        </b-button>
        <b-button
            v-if="showFollowBtn"
            variant="outline-dark"
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
        profileUuid: {
            type: String, required: true,
        },
        showProfileLink: {
            type: Boolean, default: true,
        },
    },
    computed: {
        isUserAuthenticated() {
            return this.$store.state.application.isUserAuthenticated
        },
        profile() {
            return this.$store.state.profiles.all[this.profileUuid] || null
        },
        showFollowBtn() {
            return this.isUserAuthenticated && this.profile && !this.profile.user_following
                && this.profile.id !== this.$store.state.application.currentBrowsingProfileId
        },
        showUnfollowBtn() {
            return this.isUserAuthenticated && this.profile && this.profile.user_following
                && this.profile.id !== this.$store.state.application.currentBrowsingProfileId
        },
        translations() {
            return {
                follow: gettext("Follow"),
                home: gettext("Home"),
                profile: gettext("Profile"),
                unfollow: gettext("Unfollow"),
            }
        },
    },
    created() {
        if (this.$store.state.profiles.all[this.profileUuid] === undefined) {
            this.$store.dispatch("profiles/getProfile", {uuid: this.profileUuid})
        }
    },
    methods: {
        follow() {
            this.$store.dispatch("profiles/follow", {uuid: this.profile.uuid})
        },
        unfollow() {
            this.$store.dispatch("profiles/unFollow", {uuid: this.profile.uuid})
        },
    },
}
</script>

<style scoped lang="scss">
  .socialhome-profile-reaction-buttons .btn:not(:last-child) {
    margin-right: 0.5rem;
  }
</style>
