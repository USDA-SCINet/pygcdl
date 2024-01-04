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

# Attempt to upload a geodataframe
subset_counties1 = gpd.read_file("sample_data/subset_counties1.shp")
subset_counties2 = gpd.read_file("sample_data/subset_counties2.shp")
subset_counties3 = gpd.read_file("sample_data/subset_counties3.shp")
subset_counties4 = gpd.read_file("sample_data/subset_counties4.shp")
subset_counties5 = gpd.read_file("sample_data/subset_counties5.shp")
subset_counties6 = gpd.read_file("sample_data/subset_counties6.shp")
subset_counties7 = gpd.read_file("sample_data/subset_counties7.shp")
subset_counties8 = gpd.read_file("sample_data/subset_counties8.shp")

guid1 = pygcdl_obj.upload_geometry(subset_counties1)
guid2 = pygcdl_obj.upload_geometry(subset_counties2)
guid3 = pygcdl_obj.upload_geometry(subset_counties3)
guid4 = pygcdl_obj.upload_geometry(subset_counties4)
guid5 = pygcdl_obj.upload_geometry(subset_counties5)
guid6 = pygcdl_obj.upload_geometry(subset_counties6)
guid7 = pygcdl_obj.upload_geometry(subset_counties7)
guid8 = pygcdl_obj.upload_geometry(subset_counties8)

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
# data, date data, and geometry data

print("Call 1:")
pygcdl_obj.download_polygon_subset(pandas_df, dates=dates1, \
    t_geom = guid1)
print("Call 2:")
pygcdl_obj.download_polygon_subset(matrix_df, dates=dates2, \
    t_geom = guid2)
print("Call 3:")
pygcdl_obj.download_polygon_subset(dict_df, years=years, months=months, \
    t_geom = "sample_data/subset_counties4.shp")
print("Call 4:")
pygcdl_obj.download_polygon_subset(numpy_df, years=years, days=days, \
    t_geom = "sample_data/clay_aoi.geojson")
