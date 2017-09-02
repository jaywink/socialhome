<template>
    <div>
        <h2>
            {{ title }}
            <a href="/preferences/user/">
                <span class="badge badge-default pull-right rounded-0">alpha</span>
            </a>
        </h2>
        <p>{{ helpText }}</p>
    </div>
</template>

<script>
import Vue from "vue"
import store from "streams/app/stores/applicationStore"


export default Vue.component("base-stamped-element", {
    props: {
        title: {type: String, required: true},
        helpText: {type: String, required: true}
    }
})
</script>
