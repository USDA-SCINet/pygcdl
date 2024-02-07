import sys
import pygcdl
import geopandas as gpd
import os
import pandas as pd
import numpy as np
from pathlib import Path
import pyproj

pygcdl_obj = pygcdl.PyGeoCDL()

# Upload a geometry
guid0 = pygcdl_obj.upload_geometry("sample_data/jer_bounds_sf.shp")
print(guid0)

# Load the geometry to extract the CRS
jer_bounds_sf = gpd.read_file("sample_data/jer_bounds_sf.shp")
t_crs = jer_bounds_sf.crs # EPSG:32613

# Set request parameters
resolution = 250
dates1 = "2000-01-29"

prism_df = pd.DataFrame([["PRISM", "ppt"]], columns =
    ["dataset", "variable"])

output1 = Path("output1")


# Case 1:
pygcdl_obj.download_polygon_subset(
    prism_df,
    dates=dates1, 
    t_geom=guid0,
    t_crs=t_crs,
    dsn=output1,
    )

# Case 2:
pygcdl_obj.download_polygon_subset(
    prism_df,
    dates=dates1, 
    t_geom=guid0,
    t_crs=t_crs,
    resolution=resolution,
    dsn=output1,
    )

# Case 3:
pygcdl_obj.download_polygon_subset(
    prism_df,
    dates=dates1, 
    t_geom=guid0,
    dsn=output1,
    )

# Case 4:
pygcdl_obj.download_polygon_subset(
    prism_df,
    dates=dates1, 
    t_geom=guid0,
    dsn=output1,
    resolution=resolution
    )