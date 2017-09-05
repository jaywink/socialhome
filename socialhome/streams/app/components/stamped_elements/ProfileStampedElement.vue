<template>
    <div>
        <div v-if="showProfileButtons" class="pull-right">
            <div class="dropdown text-right">
                <b-dropdown>
                    <i slot="button-content" id="profile-menu-button" class="fa fa-cog" />
                    <b-dropdown-item
                        :href="urls.updateProfile"
                        :title="translations.updateProfile"
                        :aria-label="translations.updateProfile"
                    >
                        <i class="fa fa-address-book" /> {{ translations.updateProfile }}
                    </b-dropdown-item>
                    <b-dropdown-item
                        :href="urls.pictureUpdate"
                        :title="translations.changePicture"
                        :aria-label="translations.changePicture"
                    >
                        <i class="fa fa-camera" /> {{ translations.changePicture }}
                    </b-dropdown-item>
                    <b-dropdown-item
                        :href="urls.preferences"
                        :title="translations.preferences"
                        :aria-label="translations.preferences"
                    >
                        <i class="fa fa-cog" /> {{ translations.preferences }}
                    </b-dropdown-item>
                    <b-dropdown-item
                        :href="urls.apiToken"
                        :title="translations.apiToken"
                        :aria-label="translations.apiToken"
                    >
                        <i class="fa fa-code" /> {{ translations.apiToken }}
                    </b-dropdown-item>
                    <b-dropdown-item
                        :href="urls.accountsEmail"
                        :title="translations.email"
                        :aria-label="translations.email"
                    >
                        <i class="fa fa-envelope"></i> {{ translations.email }}
                    </b-dropdown-item>
                    <b-dropdown-item
                        v-if=""
                        :href="urls.accountsEmail"
                        :title="translations.organizeProfileContent"
                        :aria-label="translations.organizeProfileContent"
                    >
                        <i class="fa fa-arrows-v"></i> {{ translations.organizeProfileContent }}
                    </b-dropdown-item>
                </b-dropdown>
            </div>
            <div class="mt-1">
                <b-button
                    variant="secondary"
                    :href="urls.contactsFollowed"
                    :title="translations.following"
                    :aria-label="translations.following"
                >
                    <i class="fa fa-user" />
                    <i class="fa fa-arrow-right" />
                    <i class="fa fa-users" />
                    &nbsp;{{ profile.followingCount }}
                </b-button>
            </div>
            <div class="mt-1">
                <b-button
                    variant="secondary"
                    href="#"
                    :title="translations.followers"
                    :aria-label="translations.followers"
                >
                    <i class="fa fa-users" />
                    <i class="fa fa-arrow-right" />
                    <i class="fa fa-user" />
                    &nbsp;{{ profile.followersCount }}
                </b-button>
            </div>
        </div>
        <div class="d-inline-block">
            <img
                v-if="profile.saferImageUrlLarge"
                class="profile-stream-stamped-image"
                :src="profile.saferImageUrlLarge"
            />
        </div>
        <div class="d-inline-block ml-3 align-center stamped-profile-info">
            <h1>{{ nameOrGuid }}</h1>
            <h3><cite :title="translations.userHandle">{{ profile.handle }}</cite></h3>
        </div>
        <div class="text-center">
            <b-button v-if="profile.pinnedContentExists" :variant="pinnedContentVariant" :href="urls.pinnedContent">
                {{ translations.pinnedContent }}
            </b-button>
            <b-button :variant="profileContentVariant" :href="urls.profileAllContent">
                {{ translations.profileAllContent }}
            </b-button>
        </div>
        <div class="clearfix" />
    </div>
</template>

<script>
import Vue from "vue"
import applicationStore from "streams/app/stores/applicationStore"


export default Vue.component("profile-stamped-element", {
    computed: {
        nameOrGuid() {
            return this.profile.name ? this.profile.name : this.profile.guid
        },
        pinnedContentVariant() {
            return this.profile.streamType === "pinned" ? "primary" : "secondary"
        },
        profileContentVariant() {
            return this.profile.streamType === "all_content" ? "primary" : "secondary"
        },
        profile() {
            return this.$store.state.applicationStore.profile
        },
        showProfileButtons() {
            return this.$store.state.applicationStore.isUserAuthenticated &&
                this.profile.id === this.$store.state.applicationStore.currentBrowsingProfileId
        },
        translations() {
            return {
                apiToken: gettext("API token"),
                changePicture: gettext("Change picture"),
                email: gettext("Email"),
                followers: gettext("Followers"),
                following: gettext("Following"),
                organizeProfileContent: gettext("Organize profile content"),
                pinnedContent: gettext("Pinned content"),
                preferences: gettext("Preferences"),
                profileAllContent: gettext("All content"),
                updateProfile: gettext("Update profile"),
                userHandle: gettext("User handle on The Federation"),
            }
        },
        urls() {
            return {
                accountsEmail: Urls["account_email"](),
                apiToken: Urls["users:api-token"](),
                contactsFollowed: Urls["users:contacts-followed"](),
                organizeProfileUrl: Urls["users:profile-organize"](),
                pictureUpdate: Urls["users:picture-update"](),
                pinnedContent: Urls["users:profile-detail"]({guid: this.profile.guid}),
                preferences: Urls["dynamic_preferences.user"](),
                profileAllContent: Urls["users:profile-all-content"]({guid: this.profile.guid}),
                updateProfile: Urls["users:profile-update"](),
            }
        },
    },
})
</script>
