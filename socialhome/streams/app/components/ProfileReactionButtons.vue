<template>
    <div>
        <b-button v-if="showProfileLink" :href="profile.url" variant="secondary" title="Profile" aria-label="Profile">
            <i class="fa fa-user"></i>
        </b-button>
        <b-button
            v-if="!profile.is_local"
            :href="profile.home_url"
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
</template>

<script>
    export default {
        name: "profile-reaction-buttons",
        data() {
            return {
                followingAuthor: this.userFollowingAuthor,
            }
        },
        props: {
            userFollowingAuthor: {type: Boolean, default: false},
            profile: {type: Object, required: true},
            showProfileLink: {type: Boolean, default: true},
        },
        computed: {
            currentBrowsingProfileId() {
                return this.$store.state.applicationStore.currentBrowsingProfileId
            },
            showFollowBtn() {
                return this.$store.state.applicationStore.isUserAuthenticated && !this.followingAuthor
            },
            showUnfollowBtn() {
                return this.$store.state.applicationStore.isUserAuthenticated && this.followingAuthor
            },
        },
        methods: {
            unfollow() {
                this.$http.post(`/api/profiles/${this.currentBrowsingProfileId}/remove_follower/`, {guid: this.profile.guid})
                    .then(() => this.followingAuthor = false)
                    .catch(err => console.error(err) /* TODO: Proper error handling */)
            },
            follow() {
                this.$http.post(`/api/profiles/${this.currentBrowsingProfileId}/add_follower/`, {guid: this.profile.guid})
                    .then(() => this.followingAuthor = true)
                    .catch(err => console.error(err) /* TODO: Proper error handling */)
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
