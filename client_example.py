import sys
import pygcdl as pygcdl
import geopandas as gpd

pygcdl_obj = pygcdl.PyGeoCDL()
#print(pygcdl_obj.getDatasets())
#bprint(pygcdl_obj.getDatasetInfo("MODIS_NDVI"))

#Sample geometry stored as clay_aoi.geojson, square polygon in Clay county, Iowa.
pygcdl_obj.uploadGeom("clay_aoi.geojson")
