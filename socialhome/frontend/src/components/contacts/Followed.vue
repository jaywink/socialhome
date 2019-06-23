<script>
import {mapActions} from "vuex"
import _contact from "./_contacts"


export default {
    name: "Followed",
    extends: _contact,
    computed: {
        title() { return "Contacts - followed" },
        contacts() { return this.followed.contacts },
        next() { return this.followed.next },
        shouldLoadMore() { return this.followed.contacts.length < this.followed.count },
    },
    methods: {...mapActions("contacts", {fetch: "contactsFollowed"})},
}
</script>

<style scoped>

</style>
