import os

from django.test import TestCase

# Create your tests here.


import numpy as np
import pandas as pd
import xlrd

data = pd.read_excel(r'./test.xls')
# col = (col for col in data.columns)
col = [col for col in data.columns]
print(col)
print(os.path.join('sa'))