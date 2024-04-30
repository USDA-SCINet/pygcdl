<<<<<<< Updated upstream
=======
'''
This code presents several ways to download a subset of PRISM data using the pygcdl interface of the GCDL API.

The first two API requests 
The first four API requests present four different ways to download the same subset of PRISM data, including two ways to specify the spatial data and two ways to specify the temporal data. The user can confirm that the data downloaded from each of the first four API calls are equivalent. The last API requests illustrates how to download point data.
'''

# First we import the necessary libraries
>>>>>>> Stashed changes
import sys
import pygcdl as pygcdl
import geopandas as gpd

pygcdl_obj = pygcdl.PyGeoCDL()
#print(pygcdl_obj.getDatasets())
#bprint(pygcdl_obj.getDatasetInfo("MODIS_NDVI"))

<<<<<<< Updated upstream
#Sample geometry stored as clay_aoi.geojson, square polygon in Clay county, Iowa.
pygcdl_obj.uploadGeom("clay_aoi.geojson")
=======
# We request information about what datasets are available, then we request 
# more information about the PRISM dataset specifically

print(pygcdl_obj.list_datasets())
print(pygcdl_obj.get_dataset_info("PRISM"))

'''
We specify the spatial extend of our requests. We can either use a GUID (an 
identifier for uploaded geometries), or a set of clip coordinates. Here, we 
will show two different ways to create a GUID for a spatial object, and one 
way to specify clip coordinates

In each case, our spatial data represents the Jornada Experimental Range 
in southern New Mexico. The file in sample_data/jer_bounds_sf.shp includes a polygon that covers the covering this region. The file sample_data/four_points.shp includes point data for the bounding box of this same region.
'''

# First, we create a GUID by creating a geopandas object, and uploading that 
# object.
jer_bounds_sf = gpd.read_file("sample_data/jer_bounds_sf.shp")
guid0 = pygcdl_obj.upload_geometry(jer_bounds_sf) # upload geodataframe
crs_jer = jer_bounds_sf.crs

# Next, we will create a GUID by directly uploading the file. 
guid1 = pygcdl_obj.upload_geometry("sample_data/jer_bounds_sf.shp")

# Lastly, we will create a GUID for point data.
point_data = gpd.read_file("sample_data/four_points.shp")
guid2 = pygcdl_obj.upload_geometry("sample_data/four_points.shp")

# Now, guid0 and guid1 both reference the same polygon information. This is just
# done to illustrate the different ways to use the upload_geometry() function. 
# In practice, only one call to upload_geometry() is needed.

# Lastly, we will create a numpy array of coordinates to represent our spatial
# clip. Users can either specify all of the coordinates of a polygon, or the 
# corners of a bounding box. These coordinates represent the bounding box of
# the jer_bounds_sf polygon, and should be read in the same CRS as the
# jer_bounds_sf polygon.

clip_coords = np.array([[324437.940,3633604.250],[358735.940,3593682.250]])

# Next, we specify the dataset and variables we will request

prism_df = pd.DataFrame(
    [["PRISM", "ppt"]], 
    columns=["dataset", "variable"])

# We specify the temporal information of our request. Note that in each
# request, we will use either the "dates" variable OR the 
# "years"/"months"/"days" variables. These two options are included to
# illustrate the different ways to specify temporal information.
dates = "2000-01-01:2000-01-03"
years = "2000"
months = "01"
days = "01:03"

# Create output directories to store downloaded data
output1 = Path("output1")
output2 = Path("output2")
output3 = Path("output3")
output4 = Path("output4")
output5 = Path("output5")

output_dirs = [output1, output2, output3, output4, output5]
for out in output_dirs:
    if not out.is_dir():
        out.mkdir()

# Testing infer_endpoint() function
# pygcdl_obj.download_subset(
#     prism_df,
#     t_geom=jer_bounds_sf,
#     dates=dates
# )

pygcdl_obj.download_subset(
    prism_df,
    t_geom=point_data,
    dates=dates
)



# # First, we request data using the "dates" string, and the guid0 object, which 
# # we got from uploading our spatial data as a geodataframe
# print("Request 1:")
# pygcdl_obj.download_polygon_subset(
#     prism_df, 
#     dates=dates, 
#     t_geom=guid0,
#     dsn=output1,
#     )

# # We can make an equivalent request by using the "years", "months", and "days"
# # variable instead of the "dates" variable.
# print("Request 2:")
# pygcdl_obj.download_polygon_subset(
#     prism_df, 
#     years=years,
#     months=months,
#     days=days, 
#     t_geom=guid0,
#     dsn=output2,
#     )

# # We can make another equivalent request by using guid1 instead of guid0.
# print("Request 3:")
# pygcdl_obj.download_polygon_subset(
#     prism_df,
#     dates=dates,
#     t_geom=guid1,
#     dsn=output3,
#     )

# # For our last polygon subset request, we use the clipping coordinates data
# # instead of a GUID. Note that the spatial data here is slightly different from
# # the spatial extent of the previous requests since the coordinates refer to the
# # bounding box of the jer_bounds_sf polygon.

# # Also, note that we must specify the t_crs variable here to ensure GCDL knows
# # what CRS the coordinates are in.
# print("Request 4:")
# pygcdl_obj.download_polygon_subset(
#     prism_df, 
#     years=years,
#     months=months,
#     days=days, 
#     t_geom=clip_coords,
#     dsn=output4,
#     t_crs=crs_jer
#     )

# # Lastly, we request PRISM data for our point data.

# print("Request 5:")
# pygcdl_obj.download_points_subset(
#     prism_df,
#     years=years,
#     months=months,
#     days=days,
#     t_geom=guid2,
#     dsn=output5,
#     t_crs=crs_jer
#     )
>>>>>>> Stashed changes
