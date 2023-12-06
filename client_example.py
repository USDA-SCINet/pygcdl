import sys
import pygcdl as pygcdl
import geopandas as gpd
import os

pygcdl_obj = pygcdl.PyGeoCDL()
print(pygcdl_obj.getDatasets())
bprint(pygcdl_obj.getDatasetInfo("MODIS_NDVI"))

#Sample geometry stored as clay_aoi.geojson, square polygon in Clay county, Iowa.
pygcdl_obj.upload_geometry("clay_aoi.geojson")
pygcdl_obj.upload_geometry("jer_bounds_sf.shp")
pygcdl_obj.upload_geometry("jer_bounds_sf.zip")