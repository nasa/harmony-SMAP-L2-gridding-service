#!/bin/sh
###############################################################################
#
# A script invoked by the test Dockerfile to run the Python `unittest` suite
# for the SMAP-L2-Gridding-Service. The script first runs the test suite,
# then it checks for linting errors.
###############################################################################

# Exit status used to report back to caller
STATUS=0

# Run the standard set of unit tests, producing JUnit compatible output
pytest --cov=smap_l2_gridder --cov=harmony_service \
       --cov-report=html:coverage/reports \
       --junitxml=tests/reports/test-results-"$(date +'%Y%m%d%H%M%S')".xml || STATUS=1

# Run pylint
pylint smap_l2_gridder harmony_service --disable=W1203
RESULT=$((3 & $?))

if [ "$RESULT" -ne "0" ]; then
    STATUS=1
    echo "ERROR: pylint generated errors"
fi

exit $STATUS
