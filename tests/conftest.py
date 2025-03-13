import sys
import os

# This adds the "src" folder which is one level up from tests.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))