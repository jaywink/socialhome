import Vue from "vue"

export default Vue.extend({
    data(){
        let noop = {render(){}}
        return {currentComponent: noop}
    },

    methods: {
        renderModal(modalComponent) {
            this.currentComponent = modalComponent
            if(this.modal){
                this.$nextTick(this.modal.show)
            }
        }
    },

    template: '<component :is="currentComponent"/>',
})
