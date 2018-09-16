<template>
    <div>
        <div class="grid-item-author-bar mt-1">
            <div @click.stop.prevent="profileBoxTrigger" class="profilebox-trigger">
                <img :src="author.image_url_small" class="grid-item-author-bar-pic" />
                {{ author.name.length ? author.name : author.fid }}
            </div>
            <div v-show="showProfileBox" class="profile-box">
                {{ author.handle.length ? author.handle : author.fid }}
                <div class="pull-right">
                    <ProfileReactionButtons
                        :profile="author"
                        :user-following="content.user_following_author"
                    />
                </div>
                <div class="clearfix"></div>
            </div>
        </div>
    </div>
</template>

<script>
import Vue from "vue"

import ProfileReactionButtons from "frontend/components/streams/ProfileReactionButtons.vue"


export default Vue.component("author-bar", {
    components: {
        ProfileReactionButtons,
    },
    props: {
        content: {type: Object, required: true},
    },
    data() {
        return {
            showProfileBox: false,
        }
    },
    computed: {
        author() {
            return this.content.author
        },
        isUserAuthenticated() {
            return this.$store.state.applicationStore.isUserAuthenticated
        },
    },
    methods: {
        profileBoxTrigger() {
            this.showProfileBox = !this.showProfileBox
        },
    },
    updated() {
        Vue.redrawVueMasonry()
    },
})
</script>

<style scoped lang="scss">
    .profilebox-trigger {
        cursor: pointer;
    }
</style>
