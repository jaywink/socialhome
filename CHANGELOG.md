## [unreleased]

### Added
* Diaspora fetch entities view is now implemented as described in [the Diaspora protocol PR](https://github.com/diaspora/diaspora_federation/issues/31).
* Content create/update editor now features a [bootstrap-markdown](http://www.codingdrama.com/bootstrap-markdown/) editor with fancy buttons. Thanks @christophehenry for the addition!
* Content deletions are now sent out to the relay system as retractions. Also, remote retractions are processed locally to clean remotely deleted content.

### Development related notes

* JavaScript unit tests are now executed using the command `grunt test`. This will launch a separate `runserver` on port 8181 and execute the tests against that. The separate `runserver` instance will be killed after the tests have been executed. Please note the configuration env variables must be exported out when running these tests as well.

### License change

As the project is still in early changes, decision have to be made about the long term license.

Any code after 12th September 2016 (last MIT [commit](c36197491e996a599bd360e2b06853bbcb121c7a)) is now licensed as [AGPLv3](https://tldrlegal.com/license/gnu-affero-general-public-license-v3-(agpl-3.0)). The more strict GNU license was chosen to promote modification upstreaming as much as possible.

## [0.0.0] - Init changelog

Supports creating and editing content, receiving content from remote nodes and publishing public content to the relay system.
