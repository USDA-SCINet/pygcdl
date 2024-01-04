import requests
import os
from pathlib import Path
import tempfile
import zipfile
import pandas as pd
import urllib.parse
import numpy as np
import geopandas as gpd
import shapely

class PyGeoCDL:
    def __init__(self, url_base=None):
        if url_base is None:
            self.url_base = 'http://127.0.0.1:8000'

    def list_datasets(self):
        """
        Retrieves the ID and name of all available GeoCDL datasets. The
        dataset information is returned as a dictionary in which the dataset
        IDs are the keys and the dataset names are the values.
        """
        r = requests.get(self.url_base + '/list_datasets')

        return {val['id']: val['name'] for val in r.json()}

    def get_dataset_info(self, dsid):
        """
        Returns all metadata for the dataset with the given dataset ID. The
        metadata are returned as a dictionary of key: value pairs.
        """

        r = requests.get(self.url_base + '/ds_info', params={'id': dsid})

        return r.json()

    def upload_geometry(self, geom):
        # This function uploads a user geometry to the GeoCDL
        # REST API and returns a geometry upload ID to use
        # in subset requests.

        # Case 1: geom is a file
        if isinstance(geom, str):
            if not Path(geom).is_file():
                raise Exception("File not found")
            file_ext = Path(geom).suffix
            if file_ext == ".geojson" or file_ext == ".zip" \
                or file_ext == ".csv":
                files = {"geom_file": (geom, open(geom, 'rb'))}
                r = requests.post(self.url_base + '/upload_geom', files=files)
                response_dict = r.json()
                return response_dict["geom_guid"]

            elif file_ext == ".shp":

                # Call utility function to zip all auxillary shapefile files 
                # together
                zip_file_path = str(self._zip_shapefiles(geom))

                files = {"geom_file": (zip_file_path, open(zip_file_path, 'rb'))}
                r = requests.post(self.url_base + '/upload_geom', files=files)
                response_dict = r.json()
                return response_dict["geom_guid"]
            else:
                raise Exception("File format not yet supported")

        # Case 2: geom is a geodataframe
        elif isinstance(geom, gpd.GeoDataFrame):
            #Best case scenario: one single polygon
            if (len(geom) == 1 and all(geom.geom_type == "Polygon")):
                with tempfile.TemporaryDirectory() as t:
                    outpath = Path(t) / "upload.shp"
                    geom.to_file(outpath)
                    geom = self.upload_geometry(str(outpath))
                return geom

            else:
                geom_union = geom.unary_union
                if geom_union.geom_type == "Polygon":
                    upload_gdf = gpd.GeoDataFrame(index=[0], crs = geom.crs, 
                        geometry=[geom_union])
                    guid = self.upload_geometry(upload_gdf)
                    return guid
                elif geom_union.geom_type == "MultiPolygon":
                    union_area = geom_union.area 
                    convex_hull = geom_union.convex_hull
                    convex_hull_area = convex_hull.area
                    ratio = union_area / convex_hull_area
                    if ratio > 0.8:
                        upload_gdf = gpd.GeoDataFrame(
                            index=[0], 
                            crs = geom.crs,
                            geometry=[convex_hull])
                        guid = self.upload_geometry(upload_gdf)
                        return guid
                    else: 
                        upload_gdf = gpd.GeoDataFrame(
                            index=range(len(geom_union.geoms)), 
                            crs = geom.crs, 
                            geometry=list(geom_union.geoms))
                        guid = [self.upload_geometry(upload_gdf[upload_gdf.index == i]) for i in range(len(upload_gdf))]
                        return guid
        else:
            raise Exception("Geometry not supported")

    def download_polygon_subset(
        self,
        dsvars,
        dates = None,
        years = None,
        months = None,
        days = None,
        t_crs = None, 
        resolution = None,
        t_geom = None,
        out_format = 'geotiff',
        grain_method = 'strict',
        validate_method = 'strict',
        ri_method = 'nearest',
        dsn = '.',
        req_name = None
    ):
        # Current status: calls helper functions and prints out results
        dsvars_string = self._format_dsvars(dsvars)
        date_string = self._format_dates(
            dates=dates, years=years, months=months, days=days
        )
        geom_string = self._format_geometry("subset_polygon", t_geom)
        print("dsvars: ", dsvars_string)
        print("dates: ", date_string)
        print("geom: ", geom_string)

    # Helper function for identifying auxillary shapefile files and compressing
    # them into a zip folder for upload

    def _zip_shapefiles(self, file: str):

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

    # Input ds is a pandas DataFrame, a numpy array, a matrix, or a 
    # dictionary containing dataset names and variable names.
    # If input is not a pandas DataFrame, convert to a DataFrame.
    # Return the url-encoded string containing dataset and variable
    # specifications.
    def _format_dsvars(self, ds):

        if isinstance(ds, pd.DataFrame):
            dsvars = ds.iloc[:,0:2]
            dsvars.columns = ["dataset", "variable"]
        elif isinstance(ds, np.ndarray):
            dsvars = pd.DataFrame(ds, columns=["dataset", "variable"])
            dsvars = dsvars.iloc[:,0:2]
        elif isinstance(ds, list):
            dsvars = pd.DataFrame(ds, columns=["dataset", "variable"])
            dsvars = dsvars.iloc[:,0:2]
        elif isinstance(ds, dict):
            dsvars = pd.DataFrame(columns=["dataset", "variable"])
            for dataset, var_list in ds.items():
                for var in var_list:
                    dsvars.loc[len(dsvars.index)] = [dataset, var]
        else:
            raise Exception("Dataset variables format not accepted")

        dsvars['variable'] = dsvars.groupby(['dataset'])['variable'].transform(lambda x : ','.join(x)) 
        dsvars = dsvars.drop_duplicates()
        dsvars = dsvars['dataset'].str.cat(dsvars['variable'], sep=':')
        output = dsvars.str.cat(sep=';')
        url_output = urllib.parse.urlparse(output)
        return(output)

    # Create string specifying dates for request
    def _format_dates(self, dates=None, years=None, months=None, days=None):
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

    # Create string representing geometry information for request
    def _format_geometry(self, endpoint, geom):
        spatial_subset = ""
        if geom is None:
            print("Geom is None")
            return spatial_subset
        elif isinstance(geom, str):
            #if geom is a guid

            if len(geom) == 36 and not "." in geom:
                spatial_subset += "&geom_guid=" + geom
            else: #assume geom is a filename, attempt to upload
                geom_guid = self.upload_geometry(geom)
                spatial_subset += "&geom_guid=" + geom_guid
        elif isinstance(geom, list) and \
            all(len(geom[i]) == 36 for i in range(len(geom))):
            for i in range(len(geom)):
                spatial_subset += "&geom_guid" + geom[i]
        else: 
            raise Exception("Geometry configuration not implemented")
        return(spatial_subset)
        
