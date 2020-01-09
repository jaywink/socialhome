<!-- CSS Spinner from loading.io (https://loading.io/css/) -->

<template>
    <div class="lds-ellipsis">
        <div />
        <div />
        <div />
        <div />
    </div>
</template>

<script>
export default {name: "LoadingElement"}
</script>

<style lang="scss" scoped>
    .lds-ellipsis {
        align-items: center;
        display: inline-flex;
        height: 1rem;
        position: relative;
        top: 2px;
        width: 56px;
    }

    .lds-ellipsis div {
        animation-timing-function: cubic-bezier(0, 1, 1, 0);
        background: #fff;
        border-radius: 50%;
        height: calc(0.7 * 1rem);
        position: absolute;
        width: calc(0.7 * 1rem);
    }
    .lds-ellipsis div:nth-child(1) {
        left: 8px;
        animation: lds-ellipsis1 0.6s infinite;
    }

    .lds-ellipsis div:nth-child(2) {
        left: 8px;
        animation: lds-ellipsis2 0.6s infinite;
    }

    .lds-ellipsis div:nth-child(3) {
        left: 25px;
        animation: lds-ellipsis2 0.6s infinite;
    }

    .lds-ellipsis div:nth-child(4) {
        left: 42px;
        animation: lds-ellipsis3 0.6s infinite;
    }

    @keyframes lds-ellipsis1 {
        0% {
            transform: scale(0);
        }
        100% {
            transform: scale(1);
        }
    }

    @keyframes lds-ellipsis3 {
        0% {
            transform: scale(1);
        }
        100% {
            transform: scale(0);
        }
    }

    @keyframes lds-ellipsis2 {
        0% {
            transform: translate(0, 0);
        }
        100% {
            transform: translate(17px, 0);
        }
    }

</style>
