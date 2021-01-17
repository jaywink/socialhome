<script>
import {mapActions} from "vuex"
import BaseContacts from "@/components/contacts/BaseContacts"

export default {
    name: "AppFollowers",
    extends: BaseContacts,
    computed: {
        title() {
            return gettext("Contacts - followers")
        },
        contacts() {
            return this.followers.contacts
        },
        next() {
            return this.followers.next
        },
        shouldLoadMore() {
            return this.followers.contacts.length < this.followers.count
        },
    },
    methods: {...mapActions("contacts", {fetch: "contactsFollowers"})},
}
</script>

<style scoped>

</style>
