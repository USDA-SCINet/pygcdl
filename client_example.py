# This script is "bug-avoidant", in that the api calls specified avoid known 
# issues that are currently being troubleshot. Removal of the CRS parameter may
# cause an Internal Server Error and cause the data to fail to download.

# This code presents four different ways to download the same subset of PRISM
# data, including two ways to specify the spatial data and two ways to specify
# the temporal data. The user can confirm that the data downloaded from each
# of the four API calls are equivalent.

import sys
import pygcdl
import geopandas as gpd
import os
import pandas as pd
import numpy as np
from pathlib import Path

pygcdl_obj = pygcdl.PyGeoCDL()

# First we request information about what datasets are available, then we
# request more information about the PRISM dataset

print(pygcdl_obj.list_datasets())
print(pygcdl_obj.get_dataset_info("PRISM"))

jer_bounds_sf = gpd.read_file("sample_data/jer_bounds_sf.shp")
crs_jer = jer_bounds_sf.crs

# Here we create guids from the same data in two ways.
# First, we upload a file, then we upload a geodataframe.
guid0 = pygcdl_obj.upload_geometry("sample_data/jer_bounds_sf.shp")
guid1 = pygcdl_obj.upload_geometry(jer_bounds_sf)


prism_df = pd.DataFrame([["PRISM", "ppt"]], columns =
    ["dataset", "variable"])

dates = "2000-01-01:2000-01-03"
years = "2000"
months = "01"
days = "01:03"

# Create output directories to store downloaded data
output1 = Path("output1")
output2 = Path("output2")
output3 = Path("output3")
output4 = Path("output4")

output_dirs = [output1, output2, output3, output4]
for out in output_dirs:
    if not out.is_dir():
        out.mkdir()

print("Call 1:")
pygcdl_obj.download_polygon_subset(
    prism_df, 
    dates=dates, 
    t_geom=guid0,
    dsn=output1,
    t_crs=crs_jer
    )

print("Call 2:")
pygcdl_obj.download_polygon_subset(
    prism_df, 
    years=years,
    months=months,
    days=days, 
    t_geom=guid0,
    dsn=output2,
    t_crs=crs_jer
    )

print("Call 3:")
pygcdl_obj.download_polygon_subset(
    prism_df,
    dates=dates,
    t_geom=guid1,
    dsn=output3,
    t_crs=crs_jer
    )

print("Call 4:")
pygcdl_obj.download_polygon_subset(
    prism_df, 
    years=years,
    months=months,
    days=days, 
    t_geom=guid1,
    dsn=output4,
    t_crs=crs_jer
    )