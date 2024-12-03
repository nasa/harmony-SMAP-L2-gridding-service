###############################################################################
#
# Test image for the Harmony-SMAP-L2-Gridding-Service. This test image uses the
# main service image as a base layer for the tests. This ensures that the
# contents of the service image are tested, preventing discrepancies between
# the service and test environments.
###############################################################################
FROM ghcr.io/nasa/harmony-smap-l2-gridding-service

# Install additional Pip requirements (for testing)
COPY tests/pip_test_requirements.txt .

RUN pip install --no-input --no-cache-dir \
	-r pip_test_requirements.txt

# Copy test directory containing Python unittest suite, test data and utilities
COPY ./tests tests

# Configure a container to be executable via the `docker run` command.
ENTRYPOINT ["/home/tests/run_tests.sh"]
