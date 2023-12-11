import os
import shutil
import pandas as pd
import numpy as np
import urllib.parse

def zip_shapefiles(file: str):

    # Store path of input file, ie /dir/to/file_name.shp
    shp_file_path = os.path.abspath(file) 
    # Store directory of input file, ie /dir/to
    base_data_dir = os.path.dirname(os.path.abspath(file)) 
    # Store input file path WITHOUT extension, ie /dir/to/file_name
    base_file_path = os.path.splitext(shp_file_path)[0] 
    # Store file name without full path specification, ie file_name
    base_file_name = os.path.splitext(
        os.path.basename(shp_file_path)
    )[0]

    # Create path names for auxiliary files by amending appropriate file
    # extension. Ensure necessary auxiliary files are present.
    dbf_file_path = base_file_path + ".dbf"
    if not os.path.isfile(dbf_file_path):
    	raise Exception("Insufficient auxiliary shapefile files")
    shx_file_path = base_file_path + ".shx"
    if not os.path.isfile(shp_file_path):
    	raise Exception("Insufficient auxiliary shapefile files")
    prj_file_path = base_file_path + ".prj"
    if not os.path.isfile(prj_file_path):
    	raise Exception("Insufficient auxiliary shapefile files")
        
    # Create a new folder for shapefiles to be zipped in
    new_data_dir = os.path.abspath(os.path.join(base_data_dir, base_file_name))
    os.mkdir(new_data_dir)
    # Copy shp file	
    base_shp_file_name = os.path.basename(file)
    shutil.copyfile(file, os.path.join(new_data_dir, base_shp_file_name))
    # Copy dbf file
    base_dbf_file_name = os.path.basename(dbf_file_path)
    shutil.copyfile(file, os.path.join(new_data_dir, base_dbf_file_name))
    # Copy shx file
    base_shx_file_name = os.path.basename(shx_file_path)
    shutil.copyfile(file, os.path.join(new_data_dir, base_shx_file_name))
    # Copy prj file
    base_prj_file_name = os.path.basename(prj_file_path)
    shutil.copyfile(file, os.path.join(new_data_dir, base_prj_file_name))
    shutil.make_archive(base_dir = new_data_dir, root_dir = base_file_path, format = 'zip', base_name = base_file_name)
    zip_file_name = base_file_name + ".zip"
    zip_file_path = os.path.join(base_data_dir, zip_file_name)
    shutil.rmtree(new_data_dir)
    return(zip_file_path)

def format_dsvars(ds):
    # ds could be a pandas df, numpy array, or a matrix
    if isinstance(ds, pd.DataFrame):
        dsvars = ds.iloc[:,0:2]
        dsvars.columns = ["dataset", "variable"]
    elif isinstance(ds, np.ndarray):
        dsvars = pd.DataFrame(ds, columns = ["dataset", "variable"])
        dsvars = dsvars.iloc[:,0:2]
    elif isinstance(ds, list):
        dsvars = pd.DataFrame(ds, columns = ["dataset", "variable"])
        dsvars = dsvars.iloc[:,0:2]
    else:
        raise Exception("Dataset variables format not accepted")

    dsvars['variable'] = dsvars.groupby(['dataset'])['variable'].transform(lambda x : ','.join(x)) 
    dsvars = dsvars.drop_duplicates()
    dsvars = dsvars['dataset'].str.cat(dsvars['variable'], sep=':')
    output = dsvars.str.cat(sep=';')
    print(output)
    return(output)

def format_dates(dates=None, years=None, months=None, days=None):
    temporal_subset = ""
    if dates is not None:
        temporal_subset = "&dates=" + ",".join(dates)
    elif dates is None:
        if years is not None:
            temporal_subset = "&years="+"".join(years)
    print(temporal_subset)
    return(temporal_subset)

def format_geometry(endpoint, geom):
    spatial_subset = ""
