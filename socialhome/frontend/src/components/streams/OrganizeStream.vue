<template>
    <div class="socialhome-organize-content">
        <div class="socialhome-organize-content-title-bar">
            <div class="shadow-sm stamped">
                <h1 class="ml-3">
                    {{ translations.organizeContent }}
                </h1>
                <b-button class="socialhome-save-button shadow-sm p-3 m-3" pill variant="primary" @click="saveContent">
                    <i class="fa fa-save mr-3 ml-3 ml-sm-0" />
                    <span class="d-none d-sm-inline">{{ translations.save }}</span>
                </b-button>
            </div>
        </div>
        <div class="socialhome-organize-content-items">
            <draggable
                v-model="contentItems"
                handle=".handle"
                @start="drag=true"
                @end="drag=false"
            >
                <div
                    v-for="content in contentItems"
                    :key="content.id"
                    class="card card-block"
                >
                    <div class="row">
                        <div class="col-sm-2">
                            <i class="handle fa fa-5x fa-arrows-alt" />
                        </div>
                        <div class="col-sm-10 organize-content--content">
                            <stream-element
                                :content="content"
                                @loadmore="checkedLoadStream"
                            />
                        </div>
                    </div>
                </div>
            </draggable>
        </div>
        <loading-element v-show="$store.state.stream.pending.contents" />
    </div>
</template>

<script>
import Vue from "vue"
import draggable from "vuedraggable"
import {STREAM_NAMES} from "@/utils/constants"
import {streamLoadableMixin} from "@/components/streams/stream-loadable-mixin"


export default {
    name: "OrganizeStream",
    components: {draggable},
    mixins: [streamLoadableMixin],
    data() {
        return {
            drag: false,
            currentContentIds: [],
        }
    },
    computed: {
        uuid() {
            return this.$store.state.application.profile.uuid
        },
        translations() {
            return {
                organizeContent: gettext("Organize content"),
                save: gettext("Save"),
            }
        },
        contentItems: {
            get() {
                const contents = []
                this.currentContentIds.forEach(id => {
                    if (this.$store.state.stream.contents[id] !== undefined) {
                        contents.push(this.$store.state.stream.contents[id])
                    }
                })
                return contents
            },
            set(value) {
                Vue.set(this, "currentContentIds", value.map(it => it.id))
            },
        },
    },
    beforeMount() {
        this.streamName = STREAM_NAMES.PROFILE_PINNED
        this.loadStream().then(() => {
            Vue.set(this, "currentContentIds", this.$store.state.stream.currentContentIds)
        })
    },
    methods: {
        saveContent() {
            const options = {
                params: {uuid: this.uuid}, data: {sort_order: this.currentContentIds},
            }
            return this.$store.dispatch("stream/updateProfilePinned", options)
        },
        checkedLoadStream() {
            if (this.drag === false) {
                this.loadStream()
            }
        },
    },
}
</script>

<style scoped>

</style>
