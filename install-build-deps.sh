#!/bin/bash
# Ensure the build environment has Cython installed before installing requirements

# Activate Render's virtual environment
source $VIRTUAL_ENV/bin/activate

# Install Cython first
pip install cython
