<template>
    <b-button
        v-if="showShareAction"
        variant="link"
        class="reaction-icons"
        @click.stop.prevent="toggleShare"
    >
        <i class="fa fa-refresh" :aria-label="translations.toggleShare" :title="translations.toggleShare" />
        &nbsp;{{ translations.toggleShare }}
    </b-button>
</template>

<script>
export default {
    name: "ShareButton",
    props: {
        content: {
            type: Object, required: true,
        },
        parentVisibility: {
            type: String, default: "public",
        },
    },
    computed: {
        showShareAction() {
            if (!this.$store.state.application.isUserAuthenticated) {
                return false
            }
            return this.parentVisibility === "public"
        },
        translations() {
            return {
                toggleShare: this.content.user_has_shared ? gettext("unshare") : gettext("share"),
                // eslint-disable-next-line object-curly-newline
            }
        },
    },
    methods: {
        toggleShare() {
            if (this.content.user_has_shared) {
                this.$store.dispatch("stream/unshareContent", {params: {id: this.content.id}})
            } else {
                this.$store.dispatch("stream/shareContent", {params: {id: this.content.id}})
            }
        },
    },
}
</script>

<style type="text/scss" scoped>
</style>
