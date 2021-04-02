<template>
    <div>
        <h2>{{ title }}</h2>
        <p>{{ helpText }}</p>
    </div>
</template>

<script>
import Vue from "vue"

export default Vue.component("TagsStampedElement", {
    computed: {
        title() {
            return gettext("Followed tags")
        },
        helpText() {
            return gettext("Content from all followed tags.")
        },
    },
})
</script>

<style scoped lang="scss">
</style>
