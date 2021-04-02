<template>
    <base-stamped-element
        :title="title"
        :help-text="helpText"
    />
</template>

<script>
import Vue from "vue"
import "@/components/streams/stamped_elements/BaseStampedElement.vue"

export default Vue.component("LimitedStampedElement", {
    computed: {
        title() {
            return gettext("Limited")
        },
        helpText() {
            return gettext("Contains non-public content where you are recipient.")
        },
    },
})
</script>
