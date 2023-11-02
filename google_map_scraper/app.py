import json
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse
import pandas as pd
import json
from gmaps_extractor import voegToeAanCollection
from fastapi.templating import Jinja2Templates
import traceback

app = FastAPI()
templates = Jinja2Templates("templates")

from selenium import webdriver
from time import sleep


def extract_columns(file, output_path):
    excel = pd.read_csv(file.file)
    result_dfs = []

    driver = webdriver.Firefox()

    driver.get("https://www.google.com/maps/search/")
    print("** sleeping for 10 secs")
    sleep(10)
    print("** sleeping done")
    print()

    i = 0
    try:
        for idx, row in excel.iterrows():
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

            result_row = pd.DataFrame({'gmaps_address': gmaps_address[0]["Address"], 'gmaps_geo': gmaps_geo[0]["Address"]}, index=[0])

            result_dfs.append(result_row)  # Append the row DataFrame to the list

    except Exception as e:
        print()
        print("** ERROR")
        print("Printing traceback and writing current data to traceback")

        traceback.print_exc()
    finally:
        print()
        print("** Quitting driver")
        driver.quit()

        if result_dfs:
            # Concatenate all DataFrames into one
            result_df = pd.concat(result_dfs, ignore_index=True)

            # Save the results to a CSV file
            result_df.to_csv(output_path, index=False)

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/scrape_google_maps/")
async def scrape_google_maps(
    background_tasks: BackgroundTasks,
    file: UploadFile,
):
    
    try:
        if file:
            # Define the output path for the resulting CSV file
            output_path = "output.csv"

            # Schedule the background task for scraping, passing the uploaded file
            background_tasks.add_task(extract_columns, file, output_path)

            return {"message": "File uploaded,  and scraping is in progress."}
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An error occurred during file processing.")