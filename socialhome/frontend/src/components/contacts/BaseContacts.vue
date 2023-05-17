<template>
    <b-container>
        <h1>{{ title | gettext }}</h1>
        <b-card-group v-for="(chunk, index) in chunks" :key="index" class="socialhome-card-deck" deck>
            <b-card
                v-for="item in chunk"
                :key="item.fid"
                :title="contactDesignation(item)"
                class="socialhome-contact-card mb-3"
            >
                <b-card-img
                    :src="item.image_url_large"
                    :alt="contactAvatarAlt(item)"
                    top
                    @error="requestProfileUpdate($event, item, icon)"
                />
                <b-card-text>{{ item.handle }}</b-card-text>

                <profile-reaction-buttons
                    slot="footer"
                    class="pull-right"
                    :profile-uuid="item.uuid"
                />
            </b-card>
        </b-card-group>
        <infinite-loading @infinite="loadMore" />
    </b-container>
</template>

<script>
import {reactive} from "vue"
import {mapGetters, mapState} from "vuex"
import _chunk from "lodash/chunk"
import profileMixin from "@/components/streams/profile-mixin"

import ProfileReactionButtons from "@/components/common/ProfileReactionButtons"

export default {
    components: {ProfileReactionButtons},
    mixins: [profileMixin],
    computed: {
        ...mapState("contacts", {
            following: state => state.following,
            followers: state => state.followers,
        }),
        ...mapGetters("profiles", ["getProfileSelection"]),
        chunks() {
            return reactive(_chunk(this.getProfileSelection(this.contacts), this.nbColumns))
        },
        contacts() {
            return []
        },
        icon() {
            return "/static/images/pony300.png"
        },
        nbColumns() {
            if (this.$deviceSize.isMinLg) {
                return 4
            }
            if (this.$deviceSize.isMinSm) {
                return 2
            }
            return 1
        },
        nextPage() { /* Override */
            return null
        },
        pageSize() {
            return this.$route.query.page_size
        },
        shouldLoadMore() { /* Override */
            return false
        },
        title() { /* Override */
            return ""
        },
    },
    methods: {
        contactAvatarAlt(contact) {
            return `${gettext("Avatar of")} ${this.contactDesignation(contact)}`
        },
        contactDesignation(contact) {
            return contact.name || contact.handle || contact.fid
        },
        fetch() { /* Override */
        },
        async loadMore($state) {
            await this.fetch({
                params: {
                    page: this.next, pageSize: this.pageSize,
                },
            })
            await this.$nextTick()
            this.shouldLoadMore ? $state.loaded() : $state.complete()
        },
    },
}
</script>

<style lang="scss">
  @import "@/styles/variables.scss";

  .socialhome-contact-card {
    color: $darker;
  }

  @media (max-device-width: $mediumDevice) {
    .socialhome-card-deck {
      flex-direction: column;
    }
  }
</style>
