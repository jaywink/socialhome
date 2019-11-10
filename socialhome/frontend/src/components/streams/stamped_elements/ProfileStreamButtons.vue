<template>
    <div>
        <div class="text-center profile-stream-buttons">
            <b-button v-if="profile.has_pinned_content" :variant="pinnedContentVariant" :href="urls.pinnedContent">
                {{ translations.pinnedContent }}
            </b-button>
            <b-button :variant="profileContentVariant" :href="urls.profileAllContent">
                {{ translations.profileAllContent }}
            </b-button>
        </div>
    </div>
</template>

<script>
export default {
    name: "ProfileStreamButtons",
    computed: {
        pinnedContentVariant() {
            return this.profile.stream_type === "pinned" ? "primary" : "outline-dark"
        },
        profileContentVariant() {
            return this.profile.stream_type === "all_content" ? "primary" : "outline-dark"
        },
        profile() {
            return this.$store.state.application.profile
        },
        translations() {
            return {
                pinnedContent: gettext("Pinned content"),
                profileAllContent: gettext("All content"),
            }
        },
        urls() {
            return {
                pinnedContent: Urls["users:profile-detail"]({uuid: this.profile.uuid}),
                profileAllContent: Urls["users:profile-all-content"]({uuid: this.profile.uuid}),
            }
        },
    },
}
</script>

<style lang="scss">
    .profile-stream-buttons {
        margin-top: 8px;
        width: 100%;

        .btn {
            width: 50%;
        }
    }
</style>
