<template>
    <base-stamped-element
        :title="title"
        :help-text="helpText"
    />
</template>

<script>
import Vue from "vue"

import "@/components/streams/stamped_elements/BaseStampedElement.vue"

export default Vue.component("PublicStampedElement", {
    computed: {
        title() {
            return gettext("Public")
        },
        helpText() {
            return gettext("Contains public content from around the network.")
        },
    },
})
</script>
