<template>
    <base-stamped-element :title="title" :help-text="helpText"/>
</template>

<script>
import Vue from "vue"

import "streams/app/components/stamped_elements/BaseStampedElement.vue"


export default Vue.component("tag-stamped-element", {
    computed: {
        title() {
            return `#${this.$store.state.tagName}`
        },
        helpText() {
            return `${gettext("All content tagged with")} #${this.$store.state.tagName}.`
        },
    },
})
</script>
