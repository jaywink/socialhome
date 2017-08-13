<template>
    <div>
        <h2>{{ $store.state.translations.stampedContent.h2 }}</h2>
        <p>{{ $store.state.translations.stampedContent.p }}</p>
    </div>
</template>

<script>
import Vue from "vue"
import store from "streams/app/stores/streamStore"


export default Vue.component("stamped-element", {store})
</script>
