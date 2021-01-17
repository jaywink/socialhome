<script>
import {mapActions} from "vuex"
import BaseContacts from "@/components/contacts/BaseContacts"

export default {
    name: "AppFollowing",
    extends: BaseContacts,
    computed: {
        title() {
            return gettext("Contacts - following")
        },
        contacts() {
            return this.following.contacts
        },
        next() {
            return this.following.next
        },
        shouldLoadMore() {
            return this.following.contacts.length < this.following.count
        },
    },
    methods: {...mapActions("contacts", {fetch: "contactsFollowing"})},
}
</script>

<style scoped>

</style>
