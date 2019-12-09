<template>
    <div class="author-bar-timestamp">
        <a :href="content.url" :title="content.timestamp" class="unstyled-link">
            {{ timestampText }}
        </a>
        <i v-if="isLimited" class="fa fa-lock mr-2" aria-hidden="true" />
    </div>
</template>

<script>
export default {
    name: "ContentTimestamp",
    props: {
        content: {
            type: Object, required: true,
        },
    },
    computed: {
        isLimited() {
            return this.content.visibility === "limited"
        },
        timestampText() {
            return this.content.edited
                ? `${this.content.humanized_timestamp} (${gettext("edited")})`
                : this.content.humanized_timestamp
        },
    },
}
</script>

<style scoped>
    .author-bar-timestamp {
        color: #B39A96;
    }
</style>
