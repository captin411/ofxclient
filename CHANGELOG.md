# Change Log
All notable changes to this project will be documented in this file.

## [2.0.2] - 2015-05-30
- Bug: fix get password on windows
- Bug: ignore unexpected chars when decoding
- Dockerfile
- Lock versions of dependencies in requirements.txt
- Force parsing backend to 'lxml' HTML

## [2.0.1] - 2016-02-11
### Added
- Use unicode instead of byte string wherever possible
- Dropping Python 2.5 support
- Adding Python 3 support
### Fixed
- Merging multiple OFX documents into one now closes tag properly.
- LICENSE file included in dist
- More runtime testing of keychain configuration

## [1.3.8] - 2013-03-26
- Allow this to work on non-unix or Google App Engine
