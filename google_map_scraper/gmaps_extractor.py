import json, sys, re, selenium
from time import sleep
from unittest import result
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from pprint import pprint
import warnings
import traceback

# ignoring append FutureWarning
warnings.simplefilter(action='ignore', category=FutureWarning)

def voegToeAanCollection(url, data):
    collectedFlag = True
    filteredData = None
    if not("window.APP_INITIALIZATION_STATE" in data):
        filteredData = json.loads(data[0:-6]).d
    else:
        start_index = data.index("window.APP_INITIALIZATION_STATE=") + 32
        end_index = data.index(";window.APP_FLAGS")
        filteredData = json.loads(data[start_index:end_index])[3][2]

    if filteredData == None:
        return

    ew = filteredData[4:]
    if ew:
        return leesCollection(ew)


def leesCollection(values):
    data = json.loads(values)[0][1]
    amount = len(data)
    page_data = []

    for i in range(amount):
        if len(data[i]) == 15:
            
            # address
            fa = ''
            if data[i][14][39] != None:
                fa = data[i][14][39]
            
            values = {
                'Address': fa
            }

            page_data.append(values)

            break # only one data point is enough

    return page_data
