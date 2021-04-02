<template>
    <div>
        <div
            v-if="showTagActions"
            class="pull-right"
        >
            <b-button
                v-if="!followingTag"
                variant="outline-dark"
                class="tag-actions-button"
                :title="translations.follow"
                :aria-label="translations.follow"
                @click.prevent="onFollowClick"
            >
                <i class="fa fa-plus" />
            </b-button>
            <b-button
                v-if="followingTag"
                variant="outline-dark"
                class="tag-actions-button"
                :title="translations.unfollow"
                :aria-label="translations.unfollow"
                @click.prevent="onUnFollowClick"
            >
                <i class="fa fa-minus" />
            </b-button>
        </div>
        <h2>{{ title }}</h2>
        <p>{{ helpText }}</p>
    </div>
</template>

<script>
import Vue from "vue"

export default Vue.component("TagStampedElement", {
    computed: {
        followingTag() {
            return this.$store.state.user.followed_tags.includes(this.name)
        },
        name() {
            return this.$store.state.stream.tag.name
        },
        title() {
            return `#${this.name}`
        },
        helpText() {
            return `${gettext("All content tagged with")} #${this.name}.`
        },
        showTagActions() {
            return this.$store.state.application.isUserAuthenticated
        },
        translations() {
            return {
                follow: gettext("Follow"),
                unfollow: gettext("Unfollow"),
            }
        },
    },
    methods: {
        onFollowClick() {
            this.$store.dispatch("stream/followTag", {params: {uuid: this.$store.state.stream.tag.uuid}}).then(() => {
                this.$store.dispatch("user/followTag", this.name)
            })
        },
        onUnFollowClick() {
            this.$store.dispatch("stream/unfollowTag", {params: {uuid: this.$store.state.stream.tag.uuid}}).then(() => {
                this.$store.dispatch("user/unfollowTag", this.name)
            })
        },
    },
})
</script>

<style scoped lang="scss">
    .tag-actions-button {
        cursor: pointer;
    }
</style>
