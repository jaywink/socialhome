const profileMixin = {
    methods: {
        requestProfileUpdate(evt, profile, icon) {
            // eslint-disable-next-line no-param-reassign
            evt.target.src = icon // TODO: parametrize this
            this.$store.dispatch("profiles/requestProfileUpdate", {uuid: profile.uuid})
        },
    },
}

export default profileMixin
