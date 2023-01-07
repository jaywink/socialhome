<template>
    <b-button
        v-if="showReplyAction"
        variant="link"
        class="reaction-icons"
        @click.stop.prevent="toggleReplyEditor"
    >
        <i class="fa fa-comment" :aria-label="translations.reply" :title="translations.reply" />
        <span>
            &nbsp;{{ translations.reply }}
        </span>
    </b-button>
</template>

<script>
export default {
    name: "ReplyButton",
    props: {
        contentType: {
            type: String, required: true,
        },
        toggleReplyEditor: {
            type: Function, default: () => {},
        },
    },
    computed: {
        showReplyAction() {
            if (!this.$store.state.application.isUserAuthenticated || this.content_type === "share") {
                return false
            }
            return true
        },
        translations() {
            return {reply: gettext("reply")}
        },
    },
}
</script>

<style type="text/scss" scoped>

</style>
