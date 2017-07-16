import Vue from "vue";
import Vuex from "vuex";
import VueResource from "vue-resource";

// Vue setup
Vue.use(Vuex);
Vue.use(VueResource);

export default new Vuex.Store({
    state: {
        translations: {
            stampedContent: {
                h2: window.templateData.stampedContent.h2,
                p: window.templateData.stampedContent.p
            }
        },
        contentList: window.templateData.contentList,
        streamName: window.templateData.streamName,
        isUserAuthentificated: window.templateData.isUserAuthentificated,
        showAuthorBar: window.templateData.showAuthorBar
    }
});
