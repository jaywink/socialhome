<template>
    <div>
        <h2>
            {{ $store.state.translations.stampedContent.h2 }}
            <a href="/preferences/user/">
                <span class="badge badge-default pull-right rounded-0">alpha</span>
            </a>
        </h2>
        <p>{{ $store.state.translations.stampedContent.p }}</p>
    </div>
</template>

<script>
import Vue from "vue"
import store from "streams/app/stores/globalStore"


export default Vue.component("stamped-element", {store})
</script>
