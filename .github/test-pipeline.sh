#!/usr/bin/env bash
# --rm to stop container if fails
act -j tests --secret-file .github/.secret-file.env --rm