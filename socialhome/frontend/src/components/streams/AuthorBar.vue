<template>
    <div>
        <div class="grid-item-author-bar mt-1">
            <div>
                <img
                    :src="author.image_url_small"
                    class="grid-item-author-bar-pic"
                    @error="requestProfileUpdate($event, author, icon)"
                >
                <div class="author-bar-name-container">
                    <popper
                        trigger="clickToToggle"
                        :options="{
                            placement: 'bottom-start'
                        }"
                    >
                        <div class="popper">
                            {{ authorFederationId }}
                            <profile-reaction-buttons :profile-uuid="author.uuid" />
                        </div>
                        <div slot="reference" class="pointer">
                            {{ authorName }}
                        </div>
                    </popper>
                    <content-timestamp :content="content" />
                    <div v-if="isShared">
                        <popper
                            trigger="clickToToggle"
                            :options="{
                                placement: 'bottom-start'
                            }"
                        >
                            <div class="popper">
                                {{ throughAuthorFederationId }}
                                <profile-reaction-buttons
                                    :profile-uuid="content.through_author.uuid"
                                />
                            </div>
                            <div slot="reference" class="pointer">
                                <i class="fa fa-refresh mr-2 shared-icon" aria-hidden="true" /> {{ throughAuthorName }}
                            </div>
                        </popper>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Popper from "vue-popperjs"
import "vue-popperjs/dist/vue-popper.css"
import ContentTimestamp from "@/components/streams/ContentTimestamp"
import ProfileReactionButtons from "@/components/common/ProfileReactionButtons.vue"
import profileMixin from "@/components/streams/profile-mixin"

export default {
    mixins: [profileMixin],
    components: {
        ContentTimestamp,
        Popper,
        ProfileReactionButtons,
    },
    props: {
        content: {
            type: Object, required: true,
        },
    },
    computed: {
        author() {
            return this.$store.state.profiles.all[this.content.author.uuid]
        },
        authorFederationId() {
            if (this.author.finger) {
                return this.author.finger
            }
            if (this.author.handle) {
                return this.author.handle
            }
            return this.author.fid
        },
        authorName() {
            if (this.author.name) {
                return this.author.name
            } if (this.author.handle) {
                return this.author.handle
            }
            return this.author.fid
        },
        icon() {
            return "/static/images/pony50.png"
        },
        isShared() {
            return this.content.through !== this.content.id
        },
        throughAuthor() {
            return this.$store.state.profiles.all[this.content.through_author.uuid]
        },
        throughAuthorFederationId() {
            if (this.throughAuthor.finger) {
                return this.throughAuthor.finger
            }
            if (this.throughAuthor.handle) {
                return this.throughAuthor.handle
            }
            return this.throughAuthor.fid
        },
        throughAuthorName() {
            if (this.throughAuthor.name) {
                return this.throughAuthor.name
            } if (this.throughAuthor.handle) {
                return this.throughAuthor.handle
            }
            return this.throughAuthor.fid || ""
        },
    },
    updated() {
        this.$redrawVueMasonry()
    },
}
</script>

<style scoped lang="scss">
    .author-bar-name-container {
        display: inline-block;
        vertical-align: middle;
    }
    .shared-icon {
        color: #B39A96;
    }
</style>
