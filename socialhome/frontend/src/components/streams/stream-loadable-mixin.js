import {mapGetters} from "vuex"
import {STREAM_NAMES} from "@/utils/constants"


const streamLoadableMixin = {
    computed: {
        ...mapGetters("stream", ["streamDetails"]),
        streamName: {
            get() {
                return this.streamDetails.name
            },
            set(value) {
                this.$store.commit("stream/setStreamFullName", value)
            },
        },
    },
    methods: {
        loadStream() {
            const options = {params: {}}
            const lastContentId = this.$store.state.stream.currentContentIds[
                this.$store.state.stream.currentContentIds.length - 1
            ]
            if (lastContentId && this.$store.state.stream.contents[lastContentId]) {
                options.params.lastId = this.$store.state.stream.contents[lastContentId].through
            }

            switch (this.streamName) {
                case STREAM_NAMES.FOLLOWED:
                    return this.$store.dispatch("stream/getFollowedStream", options)
                case STREAM_NAMES.LIMITED:
                    return this.$store.dispatch("stream/getLimitedStream", options)
                case STREAM_NAMES.LOCAL:
                    return this.$store.dispatch("stream/getLocalStream", options)
                case STREAM_NAMES.PUBLIC:
                    return this.$store.dispatch("stream/getPublicStream", options)
                case STREAM_NAMES.TAG:
                    options.params.name = this.tag
                    return this.$store.dispatch("stream/getTagStream", options)
                case STREAM_NAMES.TAGS:
                    return this.$store.dispatch("stream/getTagsStream", options)
                case STREAM_NAMES.PROFILE_ALL:
                    options.params.uuid = this.$store.state.application.profile.uuid
                    return this.$store.dispatch("stream/getProfileAll", options)
                case STREAM_NAMES.PROFILE_PINNED:
                    options.params.uuid = this.$store.state.application.profile.uuid
                    return this.$store.dispatch("stream/getProfilePinned", options)
                default:
                    return Promise.resolve
            }
        },
    },
}

export default streamLoadableMixin
export {streamLoadableMixin}
