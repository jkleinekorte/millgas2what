import pyomo.environ as pe
import pickle
import time
from utils.save_results import ResultManager
from lci import df_to_list


""" Load object"""


def load_object(filename):
    with open(filename, 'rb') as input:
        object = pickle.load(input)

    return object

# name = input("enter file name")
name = 'test_save'
s = load_object(name)
ResultManager(s)



