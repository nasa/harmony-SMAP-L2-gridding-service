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
# Ignored errors/warnings:
# W1203 - use of f-strings in log statements. This warning is leftover from
#         using ''.format() vs % notation. For more information, see:
#     	  https://github.com/PyCQA/pylint/issues/2354#issuecomment-414526879
pylint smap_l2_gridder harmony_service --disable=W1203
RESULT=$?
RESULT=$((3 & $RESULT))

if [ "$RESULT" -ne "0" ]; then
    STATUS=1
    echo "ERROR: pylint generated errors"
fi

exit $STATUS
