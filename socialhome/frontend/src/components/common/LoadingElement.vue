<!--
CSS Spinner from Jack Rugile (https://github.com/jaywink/socialhome/pull/289)
found on http://cssload.net
-->

<template>
    <div class="cssload-loader-inner">
        <div class="cssload-cssload-loader-line-wrap-wrap">
            <div class="cssload-loader-line-wrap" />
        </div>
        <div class="cssload-cssload-loader-line-wrap-wrap">
            <div class="cssload-loader-line-wrap" />
        </div>
        <div class="cssload-cssload-loader-line-wrap-wrap">
            <div class="cssload-loader-line-wrap" />
        </div>
        <div class="cssload-cssload-loader-line-wrap-wrap">
            <div class="cssload-loader-line-wrap" />
        </div>
        <div class="cssload-cssload-loader-line-wrap-wrap">
            <div class="cssload-loader-line-wrap" />
        </div>
    </div>
</template>

<script>
export default {name: "LoadingElement"}
</script>

<style lang="scss" scoped>
  .cssload-loader-inner {
    bottom: 0;
    height: 100px;
    left: 0;
    margin: 40px auto;
    opacity: 1;
    position: relative;
    right: 0;
    top: 0;
    width: 100px;

    &.hidden-loader { /* Usefull to keep loader occuping space while not being shown */
      opacity: 0;
    }
  }

  .cssload-cssload-loader-line-wrap-wrap {
    animation: cssload-spin 2300ms cubic-bezier(.175, .885, .32, 1.275) infinite;
    box-sizing: border-box;
    height: 49px;
    left: 0;
    overflow: hidden;
    position: absolute;
    top: 0;
    transform-origin: 50% 100%;
    -o-transform-origin: 50% 100%;
    -ms-transform-origin: 50% 100%;
    -webkit-transform-origin: 50% 100%;
    -moz-transform-origin: 50% 100%;
    width: 97px;
  }

  .cssload-loader-line-wrap {
    border: 4px solid transparent;
    border-radius: 100%;
    box-sizing: border-box;
    height: 97px;
    left: 0;
    margin: 0 auto;
    position: absolute;
    right: 0;
    top: 0;
    width: 97px;
  }

  .cssload-cssload-loader-line-wrap-wrap:nth-child(1) {
    animation-delay: -57.5ms;
  }

  .cssload-cssload-loader-line-wrap-wrap:nth-child(2) {
    animation-delay: -115ms;
  }

  .cssload-cssload-loader-line-wrap-wrap:nth-child(3) {
    animation-delay: -172.5ms;
  }

  .cssload-cssload-loader-line-wrap-wrap:nth-child(4) {
    animation-delay: -230ms;
  }

  .cssload-cssload-loader-line-wrap-wrap:nth-child(5) {
    animation-delay: -287.5ms;
  }

  .cssload-cssload-loader-line-wrap-wrap:nth-child(1) .cssload-loader-line-wrap {
    border-color: rgb(234, 71, 71);
    height: 88px;
    width: 88px;
    top: 7px;
  }

  .cssload-cssload-loader-line-wrap-wrap:nth-child(2) .cssload-loader-line-wrap {
    border-color: rgb(234, 234, 71);
    height: 74px;
    width: 74px;
    top: 14px;
  }

  .cssload-cssload-loader-line-wrap-wrap:nth-child(3) .cssload-loader-line-wrap {
    border-color: rgb(71, 234, 71);
    height: 60px;
    width: 60px;
    top: 20px;
  }

  .cssload-cssload-loader-line-wrap-wrap:nth-child(4) .cssload-loader-line-wrap {
    border-color: rgb(71, 234, 234);
    height: 47px;
    width: 47px;
    top: 27px;
  }

  .cssload-cssload-loader-line-wrap-wrap:nth-child(5) .cssload-loader-line-wrap {
    border-color: rgb(71, 71, 234);
    height: 33px;
    width: 33px;
    top: 34px;
  }

  @keyframes cssload-spin {
    0%, 15% {
      transform: rotate(0);
    }
    100% {
      transform: rotate(360deg);
    }
  }
</style>
