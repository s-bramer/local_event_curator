#THIS FILE IS JUST FOR TESTING CODE#
#DELETE ME!!#
import re
import pandas as pd
import time
import calendar
from datetime import date, datetime
import numpy as np

def findElements(lst1, lst2):
    return list(np.array(lst1)[lst2])

indices = [0,1]

list_of_things = ['apple','bana','plums','berry']


print(findElements(list_of_things,indices))

conns = '–;&'
#print(conns.split(';'))
print('& 'in conns)

