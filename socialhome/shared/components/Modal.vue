<template>
    <div ref="modal" class="modal fade" tabindex="-1" role="dialog" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <slot name="title" class="modal-title"></slot>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <slot></slot>
                </div>
                <div v-if="hasFooter" class="modal-footer">
                    <slot name="footer"></slot>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    import Vue from "vue"

    export default Vue.component("modal", {
        props:    {
            onShow:   {type: Function, default: () => {}},
            onShown:  {type: Function, default: () => {}},
            onHide:   {type: Function, default: () => {}},
            onHidden: {type: Function, default: () => {}}
        },
        computed: {
            hasFooter() { return this.$slots.hasOwnProperty("footer") }
        },
        mounted() {
            this.$root.modal = this
            this.$modalEl = $(this.$refs.modal)
            this.$modalEl.on("show.bs.modal", this.onShow)
            this.$modalEl.on("shown.bs.modal", this.onShown)
            this.$modalEl.on("hide.bs.modal", this.onHide)
            this.$modalEl.on("hidden.bs.modal", this.onHidden)
            this.$modalEl.modal()

        },
        methods:  {
            show() { this.$modalEl.modal("show") },
            hide() { this.$modalEl.modal("show") }
        }
    })
</script>
