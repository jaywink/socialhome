<template>
    <div class="grid-item-author-bar mt-1">
        <div @click.stop.prevent="profileBoxTrigger" class="profilebox-trigger">
            <img :src="imageUrlSmall" class="grid-item-author-bar-pic">
            {{ name }}
        </div>
        <div v-show="showProfileBox" class="profile-box">
            {{ handle }}
            <div class="pull-right">
                <a :href="absoluteUrl" class="btn btn-secondary" title="Profile" aria-label="Profile">
                    <i class="fa fa-user"></i>
                </a>
                <a v-if="isUserLocal" :href="homeUrl" class="btn btn-secondary" title="Home" aria-label="Home">
                    <i class="fa fa-home"></i>
                </a>
                <button
                    v-if="showFollowBtn"
                    class="follower-button btn btn-secondary"
                    data-action="remove_follower"
                    :data-profileid="currentBrowsingUserId"
                    :data-target="guid"
                    title="Unfollow"
                    aria-label="Unfollow"
                >
                    <i class="fa fa-minus"></i>
                </button>
                <button
                    v-if="showUnfollowBtn"
                    class="follower-button btn btn-secondary"
                    data-action="add_follower"
                    :data-profileid="currentBrowsingUserId"
                    :data-target="guid"
                    title="Follow"
                    aria-label="Follow"
                >
                    <i class="fa fa-plus"></i>
                </button>
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
            currentBrowsingUserId: {type: String, required: true},
            homeUrl: {type: String, required: true},
            absoluteUrl: {type: String, required: true},
            imageUrlSmall: {type: String, required: true},
            isUserAuthor: {type: Boolean, required: true},
            isUserLocal: {type: Boolean, required: true},
            isUserFollowingAuthor: {type: Boolean, required: true},
            isUserAuthentificated: {type: Boolean, required: true}
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
            }
        },
        methods: {
            profileBoxTrigger() {
                this.showProfileBox = !this.showProfileBox
            }
        }
    })
</script>

<style scoped lang="scss">
    .profilebox-trigger {
        cursor: pointer;
    }
</style>
