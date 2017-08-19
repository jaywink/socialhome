import "chai/register-should"
import Vue from "vue"
import BootstrapVue from "bootstrap-vue"
import AuthorBar from "../../components/AuthorBar.vue"


Vue.use(BootstrapVue)

describe("AuthorBar", () => {

    describe("computed", () => {
        describe("isUserRemote", () => {
            it("should be the opposite of property isUserLocal", () => {
                let propsData = {
                    handle: "", name: "", guid: "", currentBrowsingProfileId: "", homeUrl: "", absoluteUrl: "",
                    imageUrlSmall: "", isUserAuthor: true, isUserLocal: true, isUserFollowingAuthor: true,
                    isUserAuthentificated: true,
                }

                let target = new AuthorBar({propsData})
                target.isUserRemote.should.be.false
                propsData.isUserLocal = false
                target = new AuthorBar({propsData})
                target.isUserRemote.should.be.true
            })
        })

        describe("canFollow", () => {
            it("sould be true if user is local, authentificated and not the author", () => {
                let propsData = {
                    handle: "", name: "", guid: "", currentBrowsingProfileId: "", homeUrl: "", absoluteUrl: "",
                    imageUrlSmall: "", isUserAuthor: false, isUserLocal: true, isUserFollowingAuthor: true,
                    isUserAuthentificated: true,
                }

                let target = new AuthorBar({propsData})
                target.canFollow.should.be.true

                propsData.isUserLocal = false
                target = new AuthorBar({propsData})
                target.canFollow.should.be.false

                propsData.isUserLocal = true
                propsData.isUserAuthentificated = false
                target.canFollow.should.be.false

                propsData.isUserAuthentificated = true
                propsData.isUserAuthor = true
                target.canFollow.should.be.false
            })
        })

        describe("showFollowBtn", () => {
            let propsData

            beforeEach(() => {
                document.body.innerHTML = "<div id=\"app\"></div>"
                propsData = {
                    handle: "", name: "", guid: "", currentBrowsingProfileId: "", homeUrl: "", absoluteUrl: "",
                    imageUrlSmall: "", isUserAuthor: false, isUserLocal: true, isUserFollowingAuthor: false,
                    isUserAuthentificated: true,
                }
            })

            it("should show the follow button when the user can and is not following the author", () => {
                let target = new AuthorBar({propsData})
                target.showFollowBtn.should.be.true
                target.$mount("#app")
                document.querySelectorAll(".follow-btn").length.should.equal(1)
            })

            it("should show the unfollow button when the user can and is not following the author", () => {
                propsData.isUserFollowingAuthor = true
                let target = new AuthorBar({propsData})
                target.showUnfollowBtn.should.be.true
                target.$mount("#app")
                document.querySelectorAll(".unfollow-btn").length.should.equal(1)
            })
        })
    })
})
