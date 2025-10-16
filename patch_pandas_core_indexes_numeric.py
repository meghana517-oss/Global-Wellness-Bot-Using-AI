import pandas as pd
import sys
import types

# Create a dummy module
numeric = types.ModuleType("numeric")

# Inject a real Int64Index class from pandas
numeric.Int64Index = pd.Index

# Patch the missing module
sys.modules["pandas.core.indexes.numeric"] = numeric
