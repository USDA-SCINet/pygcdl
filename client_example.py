import sys
import pygcdl
import geopandas as gpd
import os
import pandas as pd
import numpy as np

pygcdl_obj = pygcdl.PyGeoCDL()
#print(pygcdl_obj.list_datasets())
#print(pygcdl_obj.get_dataset_info("MODIS_NDVI"))

# Upload sample geometries in various file formats

pygcdl_obj.upload_geometry("clay_aoi.geojson")
pygcdl_obj.upload_geometry("jer_bounds_sf.shp")
#pygcdl_obj.upload_geometry("jer_bounds_sf.zip")

# Currently, download_polygon_subset just runs the helper functions
# utils.format_dsvars(), and utils.format_dates() and returns the
# url-encoded strings each function generates.

# Create sample datasets containing dataset names and variables to use as test
# input for utils.format_dsvars().
pandas_df = pd.DataFrame([["MODIS_NDVI", "NDVI"], ["PRISM","ppt"], ["PRISM", "tmax"], ["MODIS_NDVI", "test_var"]], columns = ["dataset", "variable"])
numpy_df = np.array([["MODIS_NDVI", "NDVI"], ["PRISM","ppt"], ["PRISM", "tmax"], ["MODIS_NDVI", "test_var"]])
matrix_df = [["MODIS_NDVI", "NDVI"], ["PRISM","ppt"], ["PRISM", "tmax"], ["MODIS_NDVI", "test_var"]]
dict_df = {"MODIS_NDVI":["NDVI", "test_var"], "PRISM":["ppt","tmax"]}


# Create sample date data to use for utils.format_dates(). This function can
# accept datestrings, years, months, and days as either strings separated by
# commas, or as lists of strings.
dates1 = "2000-01-01:2000-02-01,2001-01-01:2001-02-01"
dates2 = ["2000:2001", "2003"]
years = "2000,2003:2004"
months = ["1", "6", "9"]
days = ["100:200"]

# Here we apply the download_polygon_subset function on various dataset/variable
# data, and on various date data
print("Call 1:")
pygcdl_obj.download_polygon_subset(pandas_df, dates=dates1)
print("Call 2:")
pygcdl_obj.download_polygon_subset(matrix_df, dates=dates2)
print("Call 3:")
pygcdl_obj.download_polygon_subset(dict_df, years=years, months=months)
print("Call 4:")
pygcdl_obj.download_polygon_subset(numpy_df, years=years, days=days)
