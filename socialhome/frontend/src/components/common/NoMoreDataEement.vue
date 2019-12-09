<template>
    <b-card :title="translations.cardTitle" class="socialhome-no-more-data" />
</template>

<script>
export default {
    name: "NoMoreDataEement",
    props: {
        text: {
            type: String, default: "No more data",
        },
    },
    computed: {
        translations() {
            return {cardTitle: gettext(this.text)}
        },
    },
}
</script>

<style scoped lang="scss">
  @import "@/styles/variables.scss";

  .socialhome-no-more-data {
    margin-bottom: 1.25rem;

    .card-title {
      color: $darker;
      margin: 0;
      padding: 0
    }
  }
</style>
