<template>
    <div class="grid-item-author-bar mt-1">
        <div @click.stop.prevent="profileBoxTrigger" class="profilebox-trigger">
            <img :src="imageUrlSmall" class="grid-item-author-bar-pic">
            {{ name }}
        </div>
        <div v-show="showProfileBox" class="profile-box">
            {{ handle }}
            <div class="pull-right">
                <b-button :href="absoluteUrl" variant="secondary" title="Profile" aria-label="Profile">
                    <i class="fa fa-user"></i>
                </b-button>
                <b-button v-if="isUserRemote" :href="homeUrl" variant="secondary" title="Home" aria-label="Home">
                    <i class="fa fa-home"></i>
                </b-button>
                <b-button
                    variant="secondary"
                    v-if="showFollowBtn"
                    class="follower-button"
                    data-action="remove_follower"
                    :data-profileid="currentBrowsingProfileId"
                    :data-target="guid"
                    title="Unfollow"
                    aria-label="Unfollow"
                >
                    <i class="fa fa-minus"></i>
                </b-button>
                <b-button
                    variant="secondary"
                    v-if="showUnfollowBtn"
                    class="follower-button"
                    data-action="add_follower"
                    :data-profileid="currentBrowsingProfileId"
                    :data-target="guid"
                    title="Follow"
                    aria-label="Follow"
                >
                    <i class="fa fa-plus"></i>
                </b-button>
            </div>
            <div class="clearfix"></div>
        </div>
    </div>
</template>

<script>
import Vue from "vue"

export default Vue.component("author-bar", {
    props: {
        handle: {type: String, required: true},
        name: {type: String, required: true},
        guid: {type: String, required: true},
        currentBrowsingProfileId: {type: String, required: true},
        homeUrl: {type: String, required: true},
        absoluteUrl: {type: String, required: true},
        imageUrlSmall: {type: String, required: true},
        isUserAuthor: {type: Boolean, required: true},
        isUserLocal: {type: Boolean, required: true},
        isUserFollowingAuthor: {type: Boolean, required: true},
        isUserAuthentificated: {type: Boolean, required: true},
    },
    data() {
        return {showProfileBox: false}
    },
    computed: {
        showFollowBtn() {
            return this.isUserAuthentificated
                    && !this.isUserLocal
                    && !this.isUserFollowingAuthor
        },
        showUnfollowBtn() {
            return this.isUserAuthentificated
                    && !this.isUserLocal
                    && this.isUserFollowingAuthor
        },
        isUserRemote: () => !this.isUserLocal,
    },
    methods: {
        profileBoxTrigger() {
            this.showProfileBox = !this.showProfileBox
        },
    },
})
</script>

<style scoped lang="scss">
    .profilebox-trigger {
        cursor: pointer;
    }
</style>
