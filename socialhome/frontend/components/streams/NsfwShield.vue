<template>
    <div v-images-loaded.on.progress="onImageLoad">
        <b-link
            v-if="!showNsfwContent"
            @click.stop.prevent="toggleNsfwShield"
            class="text-center nsfw-shield card card-block"
            href="#"
        >
            {{ nsfwBtnText }}
        </b-link>
        <div v-else class="text-center nsfw-shield">
            <a @click.stop.prevent="toggleNsfwShield" href="#">{{ nsfwBtnText }}</a>
        </div>
        <div v-show="!showNsfwContent" class="mt-2 mb-2">
            <b-link v-for="tag in tags" :key="tag" :href="getTagUrl(tag)" class="mr-2">#{{ tag }}</b-link>
        </div>
        <slot v-if="showNsfwContent" />
    </div>
</template>

<script>
import Vue from "vue"
import imagesLoaded from "vue-images-loaded"


export default Vue.component("nsfw-shield", {
    directives: {imagesLoaded},
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
        onImageLoad() {
            if (!this.$store.state.stream.single) {
                Vue.redrawVueMasonry()
            }
        },
        toggleNsfwShield() {
            this.showNsfwContent = !this.showNsfwContent
        },
        getTagUrl(name) {
            return Urls["streams:tag"]({name})
        },
    },
    updated() {
        if (!this.$store.state.stream.single) {
            Vue.redrawVueMasonry()
        }
    },
})
</script>
