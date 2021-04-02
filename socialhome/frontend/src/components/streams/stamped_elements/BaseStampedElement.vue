<template>
    <div>
        <h2>{{ title }}</h2>
        <p>{{ helpText }}</p>
    </div>
</template>

<script>
import Vue from "vue"

export default Vue.component("BaseStampedElement", {
    props: {
        title: {
            type: String, required: true,
        },
        helpText: {
            type: String, required: true,
        },
    },
})
</script>
