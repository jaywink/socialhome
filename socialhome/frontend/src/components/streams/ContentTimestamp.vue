<template>
    <div class="author-bar-timestamp">
        <a :href="content.url" :title="content.timestamp" class="unstyled-link">
            {{ timestampText }}
        </a>
        <i v-if="isLimited" class="fa fa-lock mr-2" aria-hidden="true" />
    </div>
</template>

<script>

export default {
    name: "ContentTimestamp",
    inject: ["now"],
    props: {
        content: {
            type: Object, required: true,
        },
    },
    beforeMount() {
        this.min = 60
        this.hr = this.min * 60
        this.day = this.hr * 24
        this.month = this.day * 30 // oh well...
        this.year = this.day * 365
        this.rtf = new Intl.RelativeTimeFormat(navigator.language)
    },
    computed: {
        isLimited() {
            return this.content.visibility === "limited"
        },
        timestampText() {
            const rawTimeDiff = Math.round((this.now.currentTime / 1000) - parseInt(this.content.timestamp_epoch, 10))
            let timeDiff = 0
            let period = "second"
            if (rawTimeDiff < this.min) {
                timeDiff = rawTimeDiff
            } else if (rawTimeDiff < this.hr) {
                period = "minute"
                timeDiff = Math.round(rawTimeDiff / this.min)
            } else if (rawTimeDiff < this.day) {
                period = "hour"
                timeDiff = Math.round(rawTimeDiff / this.hr)
            } else if (rawTimeDiff < this.month) {
                period = "day"
                timeDiff = Math.round(rawTimeDiff / this.day)
            } else if (rawTimeDiff < this.year) {
                period = "month"
                timeDiff = Math.round(rawTimeDiff / this.month)
            } else {
                period = "year"
                timeDiff = Math.round(rawTimeDiff / this.year)
            }
            const humanizedTimestamp = this.rtf.format(-timeDiff, period)
            return this.content.edited
                ? `${humanizedTimestamp} (${gettext("edited")})`
                : humanizedTimestamp
        },
    },
}
</script>

<style scoped>
    .author-bar-timestamp {
        color: #B39A96;
    }
</style>
