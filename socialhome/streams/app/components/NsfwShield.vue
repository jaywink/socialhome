<template>
    <div>
        <b-button
            v-if="!showNsfwContent"
            @click.stop.prevent="toggleNsfwShield"
            class="text-center nsfw-shield card card-block"
            href="#"
            variant="link"
        >
            {{ nsfwBtnText }}
        </b-button>
        <div v-else class="text-center nsfw-shield">
            <a @click.stop.prevent="toggleNsfwShield" href="#">{{ nsfwBtnText }}</a>
        </div>
        <div v-show="!showNsfwContent">
            <b-button v-for="tag in tags" :href="getTagUrl(tag)" variant="link">#{{tag}}</b-button>
        </div>
        <slot v-if="showNsfwContent" />
    </div>
</template>

<script>
import Vue from "vue"


export default Vue.component("nsfw-shield", {
    props: {
        tags: {type: Array, required: true},
    },
    data() {
        return {
            showNsfwContent: false,
        }
    },
    computed: {
        nsfwBtnText() {
            return this.showNsfwContent ? `[${gettext("Hide NSFW content")}]` : `[${gettext("Show NSFW content")}]`
        },
    },
    methods: {
        toggleNsfwShield() {
            this.showNsfwContent = !this.showNsfwContent
        },
        getTagUrl(name) {
            return Urls["streams:tag"]({name})
        },
    },
    updated() {
        Vue.redrawVueMasonry()
    },
})
</script>
