<template>
    <b-container>
        <h1>{{ title | gettext }}</h1>
        <b-card-group v-for="(chunk, index) in chunks" :key="index" class="socialhome-card-deck" deck>
            <b-card
                v-for="item in chunk"
                :key="item.fid"
                :title="contactDesignation(item)"
                :img-src="item.image_url_large"
                :img-alt="contactAvatarAlt(item)"
                img-top
                class="socialhome-contact-card mb-3"
            >
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
import {mapState} from "vuex"
import _chunk from "lodash/chunk"

import ProfileReactionButtons from "@/components/common/ProfileReactionButtons"

export default {
    components: {ProfileReactionButtons},
    computed: {
        ...mapState("contacts", {
            following: state => state.following,
            followers: state => state.followers,
        }),
        chunks() {
            return _chunk(this.contacts, this.nbColumns)
        },
        contacts() {
            return []
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
