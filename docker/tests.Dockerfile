###############################################################################
# Harmony SMAP L2 gridding test image
#
# Built on the main service image to ensure test environment matches production
# environment
#
###############################################################################
FROM ghcr.io/nasa/harmony-smap-l2-gridder

# Install additional Pip requirements (for testing)
COPY tests/pip_test_requirements.txt .

RUN pip install --no-input --no-cache-dir \
	-r pip_test_requirements.txt

# Copy test directory containing Python unittest suite, test data and utilities
COPY ./tests tests

# Configure a container to be executable via the `docker run` command.
ENTRYPOINT ["/home/tests/run_tests.sh"]
