<template>
    <div>
        <div v-if="showProfileReactionButtons" class="pull-right">
            <ProfileReactionButtons
                :profile-uuid="profile.uuid"
                :show-profile-link="false"
            />
        </div>
        <div class="clearfix" />

        <div
            v-if="showProfileButtons"
            class="pull-right text-right"
        >
            <b-dropdown right variant="outline-dark">
                <i id="profile-menu-button" slot="button-content" class="fa fa-cog" />
                <b-dropdown-item
                    :href="urls.pictureUpdate"
                    :title="translations.changePicture"
                    :aria-label="translations.changePicture"
                >
                    {{ translations.changePicture }}
                </b-dropdown-item>
                <b-dropdown-item
                    v-if="profile.has_pinned_content"
                    :href="urls.organizeProfileUrl"
                    :title="translations.organizeProfileContent"
                    :aria-label="translations.organizeProfileContent"
                >
                    {{ translations.organizeProfileContent }}
                </b-dropdown-item>
                <b-dropdown-item
                    :href="urls.updateProfile"
                    :title="translations.updateProfile"
                    :aria-label="translations.updateProfile"
                >
                    {{ translations.updateProfile }}
                </b-dropdown-item>
            </b-dropdown>
            <div class="mt-1">
                <b-button
                    variant="outline-dark"
                    :href="urls.contactsFollowing"
                    :title="translations.following"
                    :aria-label="translations.following"
                >
                    <i class="fa fa-user" />
                    <i class="fa fa-arrow-right" />
                    <i class="fa fa-users" />
                    {{ profile.following_count }}
                </b-button>
            </div>
            <div class="mt-1">
                <b-button
                    variant="outline-dark"
                    :href="urls.contactsFollowers"
                    :title="translations.followers"
                    :aria-label="translations.followers"
                >
                    <i class="fa fa-users" />
                    <i class="fa fa-arrow-right" />
                    <i class="fa fa-user" />
                    {{ profile.followers_count }}
                </b-button>
            </div>
        </div>

        <div
            v-else-if="profile.is_local"
            class="pull-right"
        >
            <div class="mt-1">
                <span
                    :title="translations.following"
                    :aria-label="translations.following"
                >
                    <i class="fa fa-user" />
                    <i class="fa fa-arrow-right" />
                    <i class="fa fa-users" />
                    {{ profile.following_count }}
                </span>
            </div>
            <div class="mt-1">
                <span
                    :title="translations.followers"
                    :aria-label="translations.followers"
                >
                    <i class="fa fa-users" />
                    <i class="fa fa-arrow-right" />
                    <i class="fa fa-user" />
                    {{ profile.followers_count }}
                </span>
            </div>
        </div>

        <div class="d-inline-block">
            <img
                class="profile-stream-stamped-image"
                :src="profile.image_url_large"
                @error="requestProfileUpdate($event, profile, icon)"
            >
        </div>
        <div class="d-inline-block align-center stamped-profile-info">
            <h1>{{ displayName }}</h1>
            <h3>
                <cite :title="translations.userHandle">{{ profileHandle }}</cite>
            </h3>
        </div>
        <div class="clearfix" />
    </div>
</template>

<script>
import Vue from "vue"

import ProfileReactionButtons from "@/components/common/ProfileReactionButtons.vue"
import profileMixin from "@/components/streams/profile-mixin"

export default Vue.component("ProfileStampedElement", {
    mixins: [profileMixin],
    components: {ProfileReactionButtons},
    computed: {
        displayName() {
            return this.profile.name ? this.profile.name : this.profile.fid
        },
        icon() {
            return "/static/images/pony300.png"
        },
        profile() {
            return this.$store.state.profiles.all[this.$store.state.application.profile.uuid]
        },
        profileHandle() {
            return this.profile.handle ? this.profile.handle : this.profile.fid
        },
        showProfileButtons() {
            return this.$store.state.application.isUserAuthenticated
                && this.profile.id === this.$store.state.application.currentBrowsingProfileId
        },
        showProfileReactionButtons() {
            return this.$store.state.application.isUserAuthenticated
                && this.profile.id !== this.$store.state.application.currentBrowsingProfileId
        },
        translations() {
            return {
                changePicture: gettext("Change picture"),
                followers: gettext("Followers"),
                following: gettext("Following"),
                organizeProfileContent: gettext("Organize profile content"),
                updateProfile: gettext("Update profile"),
                userHandle: gettext("User handle or URL on The Federation"),
            }
        },
        urls() {
            return {
                contactsFollowing: Urls["users:contacts-following"](),
                contactsFollowers: Urls["users:contacts-followers"](),
                organizeProfileUrl: Urls["users:profile-organize"](),
                pictureUpdate: Urls["users:picture-update"](),
                updateProfile: Urls["users:profile-update"](),
            }
        },
    },
})
</script>

<style lang="scss">
    .dropdown-menu-right {
        right: auto;
    }
</style>
