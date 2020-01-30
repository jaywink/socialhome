<template>
    <div v-images-loaded.on.progress="onImageLoad">
        <b-link
            v-if="!showNsfwContent"
            class="text-center nsfw-shield card card-block"
            href="#"
            @click.stop.prevent="toggleNsfwShield"
        >
            {{ nsfwBtnText }}
        </b-link>
        <div v-else class="text-center nsfw-shield">
            <a href="#" @click.stop.prevent="toggleNsfwShield">{{ nsfwBtnText }}</a>
        </div>
        <div v-show="!showNsfwContent" class="mt-2 mb-2">
            <b-link v-for="tag in tags" :key="tag" :href="getTagUrl(tag)" class="mr-2">
                #{{ tag }}
            </b-link>
        </div>
        <slot v-if="showNsfwContent" />
    </div>
</template>

<script>
import imagesLoaded from "vue-images-loaded"
import {mapGetters} from "vuex"


export default {
    name: "NsfwShield",
    directives: {imagesLoaded},
    props: {
        tags: {
            type: Array, required: true,
        },
    },
    data() {
        return {showNsfwContent: false}
    },
    computed: {
        ...mapGetters("stream", ["streamDetails"]),
        nsfwBtnText() {
            return this.showNsfwContent ? `[${gettext("Hide NSFW content")}]` : `[${gettext("Show NSFW content")}]`
        },
    },
    updated() {
        if (!this.streamDetails.single) {
            this.$redrawVueMasonry()
        }
    },
    methods: {
        onImageLoad() {
            if (!this.streamDetails.single) {
                this.$redrawVueMasonry()
            }
        },
        toggleNsfwShield() {
            this.showNsfwContent = !this.showNsfwContent
        },
        getTagUrl(name) {
            return Urls["streams:tag"]({name})
        },
    },
}
</script>
