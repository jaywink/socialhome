<template>
    <component :is="component" v-bind="boundValues" />
</template>

<script>
import _get from "lodash/get"
import {VISIBILITY_OPTIONS} from "@/components/publisher/publisher-mixin"
import EditPublisher from "@/components/publisher/EditPublisher"
import EditReplyPublisher from "@/components/publisher/EditReplyPublisher"

export default {
    name: "EditDispatcher",
    components: {
        EditPublisher, EditReplyPublisher,
    },
    props: {
        contentId: {
            type: String, required: true,
        },
    },
    computed: {
        component() {
            return this.isReply ? "EditReplyPublisher" : "EditPublisher"
        },
        boundValues() {
            const values = {
                contentId: this.contentId,
                showPreview: _get(window, ["context", "showPreview"], true),
                text: _get(window, ["context", "text"]),
            }
            if (this.isReply) {
                values.parentId = _get(window, ["context", "parent"])
            } else {
                values.federate = _get(window, ["context", "federate"], true)
                values.includeFollowing = _get(window, ["context", "includeFollowing"], false)
                values.pinned = _get(window, ["context", "pinned"], false)
                values.recipients = _get(window, ["context", "recipients"], "")
                values.visibility = _get(window, ["context", "visibility"], VISIBILITY_OPTIONS.PUBLIC.value)
            }

            return values
        },
        isReply() {
            return _get(window, ["context", "isReply"], false)
        },
    },
}
</script>
