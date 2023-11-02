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
warnings.simplefilter(action="ignore", category=FutureWarning)


def voegToeAanCollection(url, data):
    collectedFlag = True
    filteredData = None
    if not ("window.APP_INITIALIZATION_STATE" in data):
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
            fa = ""
            if data[i][14][39] != None:
                fa = data[i][14][39]

            values = {"Address": fa}

            page_data.append(values)

            break  # only one data point is enough

    return page_data


if __name__ == "__main__":
    EXCEL_FILE_PATH = "./2_nov_resultHD.xlsx"
    OUTPUT_EXCEL_PATH = "./files/Nov_gmap_output_local.xlsx"

    excel_df = pd.read_excel(EXCEL_FILE_PATH)
    result_df = pd.DataFrame({})

    driver = webdriver.Firefox()

    driver.get("https://www.google.com/maps/search/")
    print("** sleeping for 10 secs")
    sleep(10)
    print("** sleeping done")
    print()

    i = 0

    try:
        for idx, row in excel_df.iterrows():
            # print(row[ADDRESS_COLUMN])

            address = row["address"]
            geolocation = row["geo"]

            # check for na fields
            if not type(geolocation) == str:
                geolocation = ""

            # convert . to 0. for second field in geolocation
            if ",." in geolocation or ",-." in geolocation:
                substrings = geolocation.split(",")

                substrings[1] = substrings[1].replace(".", "0.")

                substrings.append(substrings[1])
                substrings[1] = ","

                geolocation = "".join(substrings)

            if not geolocation == "":
                address_url = f"https://www.google.com/maps/search/{address}"
                geolocation_url = f"https://www.google.com/maps/search/{geolocation}"

                # extract address data
                driver.get(address_url)
                gmaps_address = voegToeAanCollection(address_url, driver.page_source)

                # extract geolocation data
                driver.get(geolocation_url)
                gmaps_geo = voegToeAanCollection(geolocation_url, driver.page_source)
            else:
                address_url = f"https://www.google.com/maps/search/{address}"

                # extract address data
                driver.get(address_url)
                gmaps_address = voegToeAanCollection(address_url, driver.page_source)

                # geolocation data to empty
                gmaps_geo = [{"Address": ""}]

            if len(gmaps_address) == 0:
                print()
                print(f'** "{address}" not found, skipping ...')
                print()
                # gmaps address not found
                gmaps_address = [{"Address": ""}]

            print(gmaps_address, gmaps_geo)

            row["gmaps_address"] = gmaps_address[0]["Address"]
            row["gmaps_geo"] = gmaps_geo[0]["Address"]

            result_df = result_df.append(row, ignore_index=True)

            # i += 1
            # if i > 3:
            #   break
    except Exception as e:
        print()
        print("** ERROR")
        print("Printing traceback and writing current data to traceback")

        traceback.print_exc()
    finally:
        print()

        print("** Quiting driver")
        driver.quit()

        print("** Writing Excel file")
        result_df.to_excel(OUTPUT_EXCEL_PATH, index=False)
