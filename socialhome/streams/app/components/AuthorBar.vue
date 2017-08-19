<template>
    <div>
        <div class="grid-item-author-bar mt-1">
            <div @click.stop.prevent="profileBoxTrigger" class="profilebox-trigger">
                <img :src="imageUrlSmall" class="grid-item-author-bar-pic" />
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
        isUserAuthenticated: {type: Boolean, required: true},
    },
    data() {
        return {
            showProfileBox: false,
            _isUserFollowingAuthor: this.isUserFollowingAuthor,
        }
    },
    computed: {
        isUserRemote() {
            return !this.isUserLocal
        },
        showFollowBtn() {
            return this.canFollow && !this.$data._isUserFollowingAuthor
        },
        showUnfollowBtn() {
            return this.canFollow && this.$data._isUserFollowingAuthor
        },
        canFollow() {
            return this.isUserAuthenticated && !this.isUserAuthor
        },
    },
    methods: {
        profileBoxTrigger() {
            this.showProfileBox = !this.showProfileBox
        },
        unfollow() {
            if (!this.currentBrowsingProfileId) {
                console.error("Not logged in")
                return
            }
            this.$http.post(`/api/profiles/${this.currentBrowsingProfileId}/remove_follower/`, {guid: this.guid})
                .then(() => { this.$data._isUserFollowingAuthor = false })
                .catch(err => console.error(err) /* TODO: Proper error handling */)
        },
        follow() {
            if (!this.currentBrowsingProfileId) {
                console.error("Not logged in")
                return
            }
            this.$http.post(`/api/profiles/${this.currentBrowsingProfileId}/add_follower/`, {guid: this.guid})
                .then(() => { this.$data._isUserFollowingAuthor = true })
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
