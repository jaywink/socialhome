<template>
    <div class="container">
        <div id="new-content-container" class="hidden">
            <a href="" id="new-content-load-link" onclick="return false;">
                <b-badge pill variant="success">
                    <span id="new-content-count">0</span>
                    <span>new posts available</span>
                </b-badge>
            </a>
        </div>
        <div class="grid">
            <div class="stamped">
                <stamped-element></stamped-element>
            </div>
            <div class="grid-sizer"></div>
            <div class="gutter-sizer"></div>
            <stream-element
                class="grid-item"
                v-for="content in $store.state.contentList"
                v-bind="content"
                :key="content.id"
                :data-content-id="content.id"
                :is-user-authentificated="$store.state.isUserAuthentificated"
                :show-author-bar="$store.state.showAuthorBar"
                :current-browsing-user-id="$store.state.currentBrowsingUserId"
            >
            </stream-element>
        </div>
    </div>
</template>

<script>
    import Vue from "vue"
    import "streams/app/components/StampedElement.vue"
    import "streams/app/components/StreamElement.vue"
    import store from "streams/app/stores/streamStore"

    export default Vue.component("stream", {store})
</script>
