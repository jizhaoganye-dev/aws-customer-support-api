"""
Pytest configuration and fixtures.
"""
import sys
import os

# Add common layer to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'layers', 'common', 'python'))
