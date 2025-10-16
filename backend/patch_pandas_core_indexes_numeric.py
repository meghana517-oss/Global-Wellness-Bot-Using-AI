import sys
import types

# Create a dummy module to bypass the missing import
sys.modules['pandas.core.indexes.numeric'] = types.ModuleType('numeric')
