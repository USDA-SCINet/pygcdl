import os
import shutil
import pandas as pd
import numpy as np
import urllib.parse
import zipfile
from pathlib import Path


def zip_shapefiles(file: str):

    file = Path(file).absolute()

    suffix_list = [".shp", ".shx", ".dbf", ".prj"]

    # Create a new folder for shapefiles to be zipped in
    output_zip_dir = Path(file.with_suffix(".zip"))

    # Add each auxillary file, check to make sure they exist
    with zipfile.ZipFile(output_zip_dir, "w") as z:
        for suffix in suffix_list:
            new_file = file.with_suffix(suffix)
            if not new_file.is_file():
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), new_file)
            z.write(new_file)

    return(output_zip_dir)

def format_dsvars(ds):

    # Input ds  is a pandas DataFrame, a numpy array, a matrix, or a 
    # dictionary containing dataset names and variable names.
    # If input is not a pandas DataFrame, convert to a DataFrame.
    # Return the url-encoded string containing dataset and variable
    # specifications.
    if isinstance(ds, pd.DataFrame):
        dsvars = ds.iloc[:,0:2]
        dsvars.columns = ["dataset", "variable"]
    elif isinstance(ds, np.ndarray):
        dsvars = pd.DataFrame(ds, columns = ["dataset", "variable"])
        dsvars = dsvars.iloc[:,0:2]
    elif isinstance(ds, list):
        dsvars = pd.DataFrame(ds, columns = ["dataset", "variable"])
        dsvars = dsvars.iloc[:,0:2]
    elif isinstance(ds, dict):
        dsvars = pd.DataFrame(columns = ["dataset", "variable"])
        for dataset, var_list in ds.items():
            for var in var_list:
                dsvars.loc[len(dsvars.index)] = [dataset, var]
    else:
        raise Exception("Dataset variables format not accepted")

    dsvars['variable'] = dsvars.groupby(['dataset'])['variable'].transform(lambda x : ','.join(x)) 
    dsvars = dsvars.drop_duplicates()
    dsvars = dsvars['dataset'].str.cat(dsvars['variable'], sep=':')
    output = dsvars.str.cat(sep=';')
    return(output)

def format_dates(dates=None, years=None, months=None, days=None):
    temporal_subset = ""
    if dates is not None:
        if isinstance(dates, list):
            temporal_subset = "&dates=" + ",".join(dates)
        else:
            temporal_subset = "&dates=" + dates
    elif years is not None:
        if isinstance(years, list):
            temporal_subset = "&years="+ ",".join(years)
        else:
            temporal_subset = "&years="+ years
        if months is not None:
            if isinstance(months, list):
                temporal_subset += "&months=" + ",".join(months)
            else:
                temporal_subset += "&months=" + months
        if days is not None:
            if isinstance(days, list):
                temporal_subset += "&days=" + ",".join(days)
            else:
                temporal_subset += "&days=" + days
    return(temporal_subset)

def format_geometry(endpoint, geom):
    spatial_subset = ""
