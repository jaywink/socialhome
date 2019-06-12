<script>
import {mapActions} from "vuex"
import _contacts from "./_contacts"


export default {
    name: "Followers",
    extends: _contacts,
    computed: {
        title() { return "Contacts - followers" },
        contacts() { return this.followers.contacts },
        next() { return this.followers.next },
        shouldLoadMore() { return this.followers.contacts.length < this.followers.count },
    },
    methods: {
        ...mapActions("contacts", {fetch: "contactsFollowers"}),
    },
}
</script>

<style scoped>

</style>
