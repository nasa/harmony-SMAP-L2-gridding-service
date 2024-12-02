#!/bin/bash
###############################################################################
#
# A bash script to extract only the notes related to the most recent version of
# SMAP L2 Gridding Service from CHANGELOG.md
#
###############################################################################

CHANGELOG_FILE="CHANGELOG.md"

## captures versions
## >## v1.0.0
## >## [v1.0.0]
VERSION_PATTERN="^## [\[]v"

## captures url links
## [unreleased]:https://github.com/nasa/harmony-browse-image-generator/compare/1.2.0..HEAD
## [v1.2.0]: https://github.com/nasa/harmony-browse-image-generator/compare/1.1.0..1.2.0
LINK_PATTERN="^\[.*\].*releases/tag/.*"

# Read the file and extract text between the first two occurrences of the
# VERSION_PATTERN
result=$(awk "/$VERSION_PATTERN/{c++; if(c==2) exit;} c==1" "$CHANGELOG_FILE")

# Print the result
echo "$result" |  grep -v "$VERSION_PATTERN" | grep -v "$LINK_PATTERN"
