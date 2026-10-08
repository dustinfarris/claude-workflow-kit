#!/usr/bin/env python3
"""Stands in for claude in test/run_batch_test.py: a stage that never answers,
as a -p session waiting on a permission prompt would look from outside."""
import time

time.sleep(60)
