<template>
    <base-stamped-element
        :title="title"
        :help-text="helpText"
    />
</template>

<script>
import Vue from "vue"
import "@/components/streams/stamped_elements/BaseStampedElement.vue"

export default Vue.component("LocalStampedElement", {
    computed: {
        title() {
            return gettext("Local")
        },
        helpText() {
            return gettext("Contains content from local users.")
        },
    },
})
</script>
