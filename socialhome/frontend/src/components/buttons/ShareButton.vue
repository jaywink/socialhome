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
    },
    computed: {
        showShareAction() {
            if (!this.$store.state.application.isUserAuthenticated) {
                return false
            }
            return !this.content.user_is_author && this.content.visibility === "public"
        },
        translations() {
            return {
                toggleShare: this.content.user_has_shared ? gettext("unshare") : gettext("share"),
                // eslint-disable-next-line object-curly-newline
            }
        },
        urls() {
            return {share: Urls["api:content-share"]({pk: this.content.id})}
        },
    },
    methods: {
        share() {
            /* TODO move to store */
            this.$http.post(this.urls.share)
                .then(() => {
                    this.content.shares_count += 1
                    this.content.user_has_shared = true
                })
                .catch(() => this.$snotify.error(gettext("An error happened while sharing the content")))
        },
        toggleShare() {
            if (this.content.user_has_shared) {
                this.unshare()
            } else {
                this.share()
            }
        },
        unshare() {
            /* TODO move to store */
            this.$http.delete(this.urls.share)
                .then(() => {
                    this.content.shares_count -= 1
                    this.content.user_has_shared = false
                })
                .catch(() => this.$snotify.error(gettext("An error happened while unsharing the content")))
        },
    },
}
</script>

<style type="text/scss" scoped>
</style>
