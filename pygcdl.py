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
import datetime
import errno
from typing import Union, Optional

class PyGeoCDL:
    """Object used to interact with GeoCDL through python
    
    Args:
        url_base (Optional(str)): IP address of the server hosting the GeoCDL. Defaults to url of Ceres service node.
    """

    def __init__(self, url_base: str=None):
        if url_base is None:
            self.url_base = 'http://10.1.1.80:8000'
        else:
            # Remove trailing '/' if present
            if url_base[-1] == "/":
                url_base = url_base[0:-1]
            self.url_base = url_base

    def list_datasets(self):
        """
        Retrieves the ID and name of all available GeoCDL datasets. The
        dataset information is returned as a dictionary in which the dataset
        IDs are the keys and the dataset names are the values.
        """
        r = requests.get(self.url_base + '/list_datasets')

        return {val['id']: val['name'] for val in r.json()}

    def get_dataset_info(self, dsid:str):
        """
        Returns all metadata for the dataset with the given dataset ID. The
        metadata are returned as a dictionary of key: value pairs.
        """

        r = requests.get(self.url_base + '/ds_info', params={'id': dsid})
        print(r.url)
        print(r.json())
        return r.json()

    def upload_geometry(self, geom:Union[os.PathLike, str, gpd.GeoDataFrame]):
        """
        Uploads a user geometry to the GeoCDL REST API and returns a 
        geometry upload ID to use in subset requests.
        
        Args:
            geom (Union[os.PathLike, str, geopandas.GeoDataFrame]): Geometry to 
                upload

        Returns: 
            Union[str, list]: A Geometry Upload ID (GUID), or list of GUIDs to 
                use in subsequent requests
        """

        # Case 0: geom is a pathlike object, convert to a file path string
        if isinstance(geom, os.PathLike):
            geom = str(geom)

        # Case 1: geom is a file
        if isinstance(geom, str):
            if not Path(geom).is_file():
                raise Exception("File not found")
            file_ext = Path(geom).suffix
            if file_ext == ".geojson" or file_ext == ".zip" \
                or file_ext == ".csv":
                files = {"geom_file": (geom, open(geom, 'rb'))}
                r = requests.post(self.url_base + '/upload_geom', files=files)
                if not r.ok:
                    if 'application/json' in r.headers.get('Content-Type'):
                        raise Exception(r.json()["detail"])
                    else:
                        raise Exception(r.text)
                response_dict = r.json()
                return response_dict["geom_guid"]

            elif file_ext == ".shp":

                # Call utility function to zip all auxillary shapefile files 
                # together
                zip_file_path = str(self._zip_shapefiles(geom))

                files = {"geom_file": (zip_file_path, open(zip_file_path, 'rb'))}
                r = requests.post(self.url_base + '/upload_geom', files=files)
                if not r.ok:
                    print(r.status_code)
                    if 'application/json' in r.headers.get('Content-Type'):
                        raise Exception(r.json()["detail"])
                    else:
                        raise Exception(r.text)
                response_dict = r.json()
                return response_dict["geom_guid"]
            else:
                raise Exception("File format not yet supported")

        # Case 2: geom is a geodataframe
        elif isinstance(geom, gpd.GeoDataFrame):
            # Easy case: Either point data or a single polygon
            if ((len(geom) == 1 and all(geom.geom_type == "Polygon")) or \
                all(geom.geom_type == "Point")):
                with tempfile.TemporaryDirectory() as t:
                    outpath = Path(t) / "upload.shp"
                    geom.to_file(outpath)
                    geom = self.upload_geometry(str(outpath))
                return geom

            else: # Hard case: geom contains multiple polygons
                # This could be either multiple rows of Polygons, or any number
                # of MultiPolygons
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
        dsvars: Union[pd.DataFrame, np.ndarray, list, dict],
        dates: Optional[Union[list[str], str]] = None,
        years: Optional[Union[list[str], str]] = None,
        months:  Optional[Union[list[str], str]] = None,
        days: Optional[Union[list[str], str]] = None,
        t_crs: Optional[str] = None, 
        resolution: Optional[float] = None,
        t_geom: Optional[Union[str, list[str], gpd.GeoDataFrame, np.ndarray]] = None,
        out_format: str = 'geotiff',
        grain_method: str = 'strict',
        validate_method: str = 'strict',
        ri_method: str = 'nearest',
        dsn: Union[str, os.PathLike] = '.',
        req_name: str = None
    ):
        """Download raster data clipped to polygon boundaries

        Args:
            dsvars (Union[pandas.DataFrame, numpy.ndarray, list, dict]):    
                The GeoCDL dataset and variable IDs requested. Use `list_datasets()` and `get_dataset_info()` to see available datasets and variables. If specified as a `pandas.DataFrame` or a `numpy.ndarray`, then list one row per variable with the first column representing the dataset ID and the second column representing the variable ID. If specified as a list, each element must be a list itself containing the dataset ID, followed by the variable ID. If specified as a dict, then list each dataset ID is a key linking to a list of variable IDs.
            dates (Optional[Union[list[str], str]]): List of dates requested.
                Each individual date is specified as a string. Ranges of dates can be specified with a colon, for example "2000-01-01:2000-01-31". User can specify multiple dates or multiple date ranges either by separating with a comma, or putting each individual date or range in a list. For example, "2000-01-01,2000-01-02" and ["2000-01-01", "2000-01-02"] are equivalent.
            years (Optional[str]): List of years requested. 
                Can include year ranges. Individual years or year ranges are comma separated. For example, "2000,2005:2008". Ignored if `dates` is specified.
            months (Optional[str]): List of months requested. 
                Individual months and month ranges are comma separated. Each month is applied to each year. For example, if `years="2000:2001"`, and `months="7:8"`, then the user is requesting July and August of 2000 and 2001. Ignored if `dates` is specified.
            days (Optional[str]): List of days requested. 
                Individual days and day ranges are comma separated. If `months` is specified, then `days` represents the day of the month. If `months` is not specified, then `days` represents the days of the year. Ignored if `dates` is specified.
            t_crs (Optional[str]): Target CRS. 
                Also used as the crs of the uploaded geometry if no geographic metadata is included in geometry (ie if user uploads clipping coordinates or a geojson file).
            resolution (Optional[str]): 
                Desired output resolution in units of the output CRS.
            t_geom (Optional[Union[str, list[str], geopandas.GeoDataFrame, numpy.ndarray]]):
                The polygon of interest, specified as either a Geometry Upload ID (GUID), and list of GUIDs, a geopandas.GeoDataFrame, or a numpy.ndarray specifying x and y coordinates of a clipping polygon. If only two clipping coordinates are provided, then they are assumed to be opposite corners of a bounding box. Clipping coordinates are assumed to be in the crs specified by `t_crs` if specified, and if not, are assumed to be in the crs of the first requested dataset. If t_geom is not set, GeoCDL returns the entire spatial extent of the dataset.
            out_format (Optional[str]): Desired format of output files.
                Choose from "geotiff" or "netcdf". Default value is "geotiff".
            grain_method (Optional[str]):
                If not all datasets you request have the same temporal grain, e.g. you request monthly data but one dataset only has daily data or only has annual data, you can specify `grain_method` to choose an alternative temporal grain. Default is "strict". Options include: 

                    * **"strict"**: User will only accept the requested date grain. If date grain is not available, GCDL will throw an error. 
                    * **"skip"**: If date grain is not available, do not return data for that dataset and variable. Will not throw an error. 
                    * **"finer"**: User will accept the requested date grain, or a finer date grain. Finer grains attempted in order from largest to smallest. Ex: if user requests annual date grain and the finer grain method, and annual data is not available, GCDL will first see if monthly data is available, and if not will then try daily data. 
                    * **"coarser"**: User will accept the requested date grain, or a coarser date grain. Coarser grains attempted in order from smallest to largest. 
                    * **"any"**: User will accept any alternative date grain. Alternative grains are attempted from largest to smallest.
            validate_method (Optional[str]):
                How to handle requested dates outside of requested dataset available data range. If "strict" (default), an error will be returned. If "overlap", the requested dates will be truncated to the date range available in all requested datasets. If "all", then the requested dates will be truncated to the available date range per dataset. Non-temporal datasets are always returned.
            ri_method (Optional[str]):
                Resampling or interpolation method used for reprojection. Resampling methods apply to polygon requests, and interpolation methods apply to point requests. Resampling method options include "nearest", "bilinear", "cubic", "cubic-spline", "lanczos", "average", or "mode". Interpolation method options include "nearest" and "linear". Default is "nearest". Only used if target CRS and/or spatial resolution are provided, otherwise data is returned in the CRS of the dataset and no reprojection is needed. If two methods are provided (comma separated, e.g. "bilinear,nearest"), the first will be used for continuous variables and the second will be used for categorical variables. An error will be returned when methods requested for categorical variables are not applicable.
            dsn (Optional[Union[str, os.PathLike]]):
                Destination for downloaded files. Default is current working directory.
            req_name (Optional[str]):
                The request name. Used to name the folder containing the downloaded data. If not set, the output directory is named "gcdl_subset" plus a timestamp of the request.



        Returns:
            str: A list of downloaded filenames.
        """

        endpoint = 'subset_polygon'

        q_str, param_dict = self._format_subset_query(
            dsvars=dsvars, 
            endpoint=endpoint,
            dates=dates, 
            years=years, 
            months=months, 
            days=days, 
            t_crs=t_crs, 
            resolution=resolution, 
            t_geom=t_geom,
            out_format=out_format, 
            grain_method=grain_method,
            validate_method=validate_method,
            ri_method=ri_method)

        out_files = self._submit_subset_query(q_str, param_dict, dsn, req_name)
        return out_files

    def download_points_subset(
        self,
        dsvars: Union[pd.DataFrame, np.ndarray, list, dict],
        dates: Optional[Union[list[str], str]] = None,
        years: Optional[str] = None,
        months: Optional[str] = None,
        days: Optional[str] = None,
        t_crs: Optional[str] = None, 
        t_geom: Optional[Union[str, list[str], gpd.GeoDataFrame]] = None,
        out_format: Optional[str] = 'csv',
        grain_method: Optional[str] = 'strict',
        validate_method: Optional[str] = 'strict',
        ri_method: Optional[str] = 'nearest',
        dsn: Optional[Union[str, os.PathLike]] = '.',
        req_name: Optional[str] = None
    ):
        """Download point-based data

        Args:
            dsvars (Union[pandas.DataFrame, numpy.ndarray, list, dict]):    
                The GeoCDL dataset and variable IDs requested. Use `list_datasets()` and `get_dataset_info()` to see available datasets and variables. If specified as a `pandas.DataFrame` or a `numpy.ndarray`, then list one row per variable with the first column representing the dataset ID and the second column representing the variable ID. If specified as a list, each element must be a list itself containing the dataset ID, followed by the variable ID. If specified as a dict, then list each dataset ID is a key linking to a list of variable IDs.
            dates (Optional[Union[list[str], str]]): List of dates requested.
                Each individual date is specified as a string. Ranges of dates can be specified with a colon, for example "2000-01-01:2000-01-31". User can specify multiple dates or multiple date ranges either by separating with a comma, or putting each individual date or range in a list. For example, "2000-01-01,2000-01-02" and ["2000-01-01", "2000-01-02"] are equivalent.
            years (Optional[str]): List of years requested. 
                Individual years and year ranges and year ranges are comma separated. For example, "2000,2005:2008". Ignored if `dates` is specified.
            months (Optional[str]): List of months requested. 
                Individual months and month ranges are comma separated. Each month is applied to each year. For example, if `years="2000:2001"`, and `months="7:8"`, then the user is requesting July and August of 2000 and 2001. Ignored if `dates` is specified.
            days (Optional[str]): List of days requested. 
                Individual days and day ranges are comma separated. If `months` is specified, then `days` represents the day of the month. If `months` is not specified, then `days` represents the days of the year. Ignored if `dates` is specified.
            t_crs (Optional[str]): Target CRS. 
                Also used as the crs of the uploaded geometry if no geographic metadata is included in geometry (ie if user uploads a geojson file).
            t_geom (Optional[Union[str, list[str], geopandas.GeoDataFrame]]):
                The points geometry of interest, specified as either a Geometry Upload ID (GUID), and list of GUIDs, or a geopandas.GeoDataFrame. If t_geom is not set, GeoCDL returns the entire spatial extent of the dataset.
            out_format (Optional[str]): Desired format of output files.
                Choose from "csv", "shapefile" or "netcdf". Default value is "csv".
            grain_method (Optional[str]):
                If not all datasets you request have the same temporal grain, e.g. you request monthly data but one dataset only has daily data or only has annual data, you can specify `grain_method` to choose an alternative temporal grain. Default is "strict". Options include: 

                    * **"strict"**: User will only accept the requested date grain. If date grain is not available, GCDL will throw an error. 
                    * **"skip"**: If date grain is not available, do not return data for that dataset and variable. Will not throw an error. 
                    * **"finer"**: User will accept the requested date grain, or a finer date grain. Finer grains attempted in order from largest to smallest. Ex: if user requests annual date grain and the finer grain method, and annual data is not available, GCDL will first see if monthly data is available, and if not will then try daily data. 
                    * **"coarser"**: User will accept the requested date grain, or a coarser date grain. Coarser grains attempted in order from smallest to largest. 
                    * **"any"**: User will accept any alternative date grain. Alternative grains are attempted from largest to smallest.
            validate_method (Optional[str]):
                How to handle requested dates outside of requested dataset available data range. If "strict" (default), an error will be returned. If "overlap", the requested dates will be truncated to the date range available in all requested datasets. If "all", then the requested dates will be truncated to the available date range per dataset. Non-temporal datasets are always returned.
            ri_method (Optional[str]):
                Resampling or interpolation method used for reprojection. Resampling methods apply to polygon requests, and interpolation methods apply to point requests. Resampling method options include "nearest", "bilinear", "cubic", "cubic-spline", "lanczos", "average", or "mode". Interpolation method options include "nearest" and "linear". Default is "nearest". Only used if target CRS and/or spatial resolution are provided, otherwise data is returned in the CRS of the dataset and no reprojection is needed. If two methods are provided (comma separated, e.g. "bilinear,nearest"), the first will be used for continuous variables and the second will be used for categorical variables. An error will be returned when methods requested for categorical variables are not applicable.
            dsn (Optional[Union[str, os.PathLike]]):
                Destination for downloaded files. Default is current working directory.
            req_name (Optional[str]):
                The request name. Used to name the folder containing the downloaded data. If not set, the output directory is named "gcdl_subset" plus a timestamp of the request.



        Returns:
            str: A list of downloaded filenames.
        """

        endpoint = 'subset_points'
        q_str, param_dict = self._format_subset_query(
            dsvars=dsvars, 
            endpoint=endpoint,
            dates=dates, 
            years=years, 
            months=months, 
            days=days, 
            t_crs=t_crs, 
            t_geom=t_geom,
            out_format=out_format, 
            grain_method=grain_method,
            validate_method=validate_method,
            ri_method=ri_method)

        out_files = self._submit_subset_query(q_str, param_dict, dsn, req_name)
        return out_files
    
    def download_subset(
        self,
        dsvars,
        dates = None,
        years = None,
        months = None,
        days = None,
        t_crs = None,
        resolution = None,
        t_geom = None,
        out_format = None,
        grain_method = 'strict',
        validate_method = 'strict',
        ri_method = 'nearest',
        dsn = '.',
        req_name = None
    ):
        """Download point or raster data depending on inferred geometry type.

        Args:
            dsvars (Union[pandas.DataFrame, numpy.ndarray, list, dict]):    
                The GeoCDL dataset and variable IDs requested. Use `list_datasets()` and `get_dataset_info()` to see available datasets and variables. If specified as a `pandas.DataFrame` or a `numpy.ndarray`, then list one row per variable with the first column representing the dataset ID and the second column representing the variable ID. If specified as a list, each element must be a list itself containing the dataset ID, followed by the variable ID. If specified as a dict, then list each dataset ID is a key linking to a list of variable IDs.
            dates (Optional[Union[list[str], str]]): List of dates requested.
                Each individual date is specified as a string. Ranges of dates can be specified with a colon, for example "2000-01-01:2000-01-31". User can specify multiple dates or multiple date ranges either by separating with a comma, or putting each individual date or range in a list. For example, "2000-01-01,2000-01-02" and ["2000-01-01", "2000-01-02"] are equivalent.
            years (Optional[str]): List of years requested. 
                Can include year ranges. Individual years or year ranges are comma separated. For example, "2000,2005:2008". Ignored if `dates` is specified.
            months (Optional[str]): List of months requested. 
                Individual months and month ranges are comma separated. Each month is applied to each year. For example, if `years="2000:2001"`, and `months="7:8"`, then the user is requesting July and August of 2000 and 2001. Ignored if `dates` is specified.
            days (Optional[str]): List of days requested. 
                Individual days and day ranges are comma separated. If `months` is specified, then `days` represents the day of the month. If `months` is not specified, then `days` represents the days of the year. Ignored if `dates` is specified.
            t_crs (Optional[str]): Target CRS. 
                Also used as the crs of the uploaded geometry if no geographic metadata is included in geometry (ie if user uploads clipping coordinates or a geojson file).
            resolution (Optional[str]): 
                Desired output resolution in units of the output CRS. Ignored for point data.
            t_geom (Optional[Union[str, list[str], geopandas.GeoDataFrame, numpy.ndarray]]):
                The polygon of interest, specified as either a Geometry Upload ID (GUID), and list of GUIDs, a geopandas.GeoDataFrame, or a numpy.ndarray specifying x and y coordinates of a clipping polygon. If only two clipping coordinates are provided, then they are assumed to be opposite corners of a bounding box. Clipping coordinates are assumed to be in the crs specified by `t_crs` if specified, and if not, are assumed to be in the crs of the first requested dataset. If t_geom is not set, GeoCDL returns the entire spatial extent of the dataset.
            out_format (Optional[str]): Desired format of output files.
                For polygon data, choose between "geotiff" (default) or "netcdf". For point data, choose between "csv" (default), "shapefile", or "netcdf".
            grain_method (Optional[str]):
                If not all datasets you request have the same temporal grain, e.g. you request monthly data but one dataset only has daily data or only has annual data, you can specify `grain_method` to choose an alternative temporal grain. Default is "strict". Options include: 

                    * **"strict"**: User will only accept the requested date grain. If date grain is not available, GCDL will throw an error. 
                    * **"skip"**: If date grain is not available, do not return data for that dataset and variable. Will not throw an error. 
                    * **"finer"**: User will accept the requested date grain, or a finer date grain. Finer grains attempted in order from largest to smallest. Ex: if user requests annual date grain and the finer grain method, and annual data is not available, GCDL will first see if monthly data is available, and if not will then try daily data. 
                    * **"coarser"**: User will accept the requested date grain, or a coarser date grain. Coarser grains attempted in order from smallest to largest. 
                    * **"any"**: User will accept any alternative date grain. Alternative grains are attempted from largest to smallest.
            validate_method (Optional[str]):
                How to handle requested dates outside of requested dataset available data range. If "strict" (default), an error will be returned. If "overlap", the requested dates will be truncated to the date range available in all requested datasets. If "all", then the requested dates will be truncated to the available date range per dataset. Non-temporal datasets are always returned.
            ri_method (Optional[str]):
                Resampling or interpolation method used for reprojection. Resampling methods apply to polygon requests, and interpolation methods apply to point requests. Resampling method options include "nearest", "bilinear", "cubic", "cubic-spline", "lanczos", "average", or "mode". Interpolation method options include "nearest" and "linear". Default is "nearest". Only used if target CRS and/or spatial resolution are provided, otherwise data is returned in the CRS of the dataset and no reprojection is needed. If two methods are provided (comma separated, e.g. "bilinear,nearest"), the first will be used for continuous variables and the second will be used for categorical variables. An error will be returned when methods requested for categorical variables are not applicable.
            dsn (Optional[Union[str, os.PathLike]]):
                Destination for downloaded files. Default is current working directory.
            req_name (Optional[str]):
                The request name. Used to name the folder containing the downloaded data. If not set, the output directory is named "gcdl_subset" plus a timestamp of the request.



        Returns:
            str: A list of downloaded filenames.
        """
        endpoint = self._infer_endpoint(t_geom)
        print("Endpoint = ", endpoint)
        if endpoint == "subset_polygon":
            out_files = self.download_polygon_subset(
                dsvars,
                dates, 
                years, 
                months, 
                days,
                t_crs, 
                resolution, 
                t_geom,
                out_format,
                grain_method, 
                validate_method,
                ri_method,
                dsn, 
                req_name
            )
        elif endpoint == "subset_points":
            if resolution is not None:
                raise Exception("Resolution parameter not applicable for point extraction")
            out_files = self.download_points_subset(
                dsvars,
                dates, 
                years, 
                months, 
                days,
                t_crs,
                resolution, 
                t_geom,
                out_format,
                grain_method, 
                validate_method,
                ri_method,
                dsn, 
                req_name
            )
        else:
            raise Exception("Unknown endpoint")
        return out_files

    def _format_subset_query(
        self,
        dsvars,
        endpoint,
        dates=None,
        years=None,
        months=None,
        days=None,
        t_crs=None, 
        resolution=None,
        t_geom=None,
        out_format='geotiff',
        grain_method='strict',
        validate_method='strict',
        ri_method='nearest',
    ):

        get_params_dict = {}

         # Format datasets and variables into string
        dv_str = self._format_dsvars(dsvars)
        get_params_dict.update(dv_str)

        # Format user geometry
        spatial_subset = self._format_geometry(endpoint, t_geom)
        get_params_dict.update(spatial_subset)

        # Format spatial parameters (crs, resolution, interpolation/resampling method)
        spatial_parameters = self._format_spatial_parameters(
            endpoint, 
            ri_method, 
            t_crs, 
            resolution
        )
        get_params_dict.update(spatial_parameters)

        # Format temporal subset instructions
        temporal_subset = self._format_dates(dates, years, months, days)
        get_params_dict.update(temporal_subset)

        # Temporal parameters (grain method, validate method)
        temporal_parameters = self._format_temporal_parameters(
            grain_method, 
            validate_method
        )
        get_params_dict.update(temporal_parameters)

        # Other parameters
        other_parameters = {}
        if out_format is not None:
            other_parameters['output_format'] = out_format
        get_params_dict.update(other_parameters)
        
        
        # Build query
        query_str = self.url_base + "/" + endpoint

        return query_str, get_params_dict

    def _submit_subset_query(self, query_str, param_dict, dsn, req_name):
        # dsn = path to directory
        # req_name = name of folder to put in dsn, with downloaded data
        if not Path(dsn).is_dir():
            raise Exception("Destination folder DNE")

        dsn = Path(dsn)

        # Create output zip file path, based on time and date of creation
        if req_name is None:
            basename = "gcdl_subset"
            suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
            output_dir = "_".join([basename, suffix])
        
        # Check to see if EITHER clip for geom_guid is provided.
        # Set num_queries equal to the number of geometries.
        # Request can have multiple geometries if user submitted a multipolygon
        GUID = False
        if "geom_guid" in param_dict.keys():
            GUID = True
            spatial_params = param_dict["geom_guid"]
            if isinstance(spatial_params, str):
                param_dict["geom_guid"] = [spatial_params]
                num_queries = 1
            elif isinstance(spatial_params, list):
                num_queries = len(spatial_params)
        elif "clip" in param_dict.keys():
            num_queries = 1
        else:
            raise Exception("No query provided")
            return

        out_files = []
        headers = {"accept": "application/json"}

        for q in range(num_queries):
            out = output_dir + "_" + str(q+1)
            subset_dir = Path(dsn) / Path(out)
            subset_zip = Path(str(subset_dir) + ".zip")
            params = param_dict.copy()
            if GUID: # Iterate through possible list of GUIDs
                req_spatial = param_dict["geom_guid"][q]
                params["geom_guid"] = req_spatial
            r = requests.get(query_str, params=params, headers=headers)
            print(r.url)
            if not r.ok:
                print("Status_code: ", r.status_code)
                if 'application/json' in r.headers.get('Content-Type'):
                    raise Exception(r.json()["detail"])
                else:
                    raise Exception(r.text)
            else:
                # Write contents to zip file in chunks
                with open(subset_zip, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        f.write(chunk)
                # Unzip subset_zip
                with zipfile.ZipFile((str(subset_zip)), 'r') as f:
                    print("Files downloaded and unzipped: ", f.namelist())
                    file_names = f.namelist()
                    # add output directory to file name
                    file_names_out = [str(Path(dsn / k)) for k in f.namelist()]
                    out_files.extend(file_names_out)
                    f.extractall(Path(dsn))
        return out_files

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
                z.write(new_file, arcname=new_file.name)

        return(output_zip_dir)

    # Input ds is a pandas DataFrame, a numpy array, a matrix, or a 
    # dictionary containing dataset names and variable names.
    # If input is not a pandas DataFrame, convert to a DataFrame.
    # Return the url-encoded string containing dataset and variable
    # specifications.
    def _format_dsvars(self, dsvars):

        if isinstance(dsvars, pd.DataFrame):
            dsvars = dsvars.iloc[:,0:2]
            dsvars.columns = ["dataset", "variable"]
        elif isinstance(dsvars, np.ndarray):
            dsvars = pd.DataFrame(dsvars, columns=["dataset", "variable"])
            dsvars = dsvars.iloc[:,0:2]
        elif isinstance(dsvars, list):
            dsvars = pd.DataFrame(dsvars, columns=["dataset", "variable"])
            dsvars = dsvars.iloc[:,0:2]
        elif isinstance(dsvars, dict):
            dsvars_out = pd.DataFrame(columns=["dataset", "variable"])
            for dataset, var_list in dsvars.items():
                for var in var_list:
                    dsvars_out.loc[len(dsvars_out.index)] = [dataset, var]
            dsvars = dsvars_out
        else:
            raise Exception("Dataset variables format not accepted")

        dsvars['variable'] = dsvars.groupby(['dataset'])['variable'].transform(lambda x : ','.join(x)) 
        dsvars = dsvars.drop_duplicates()
        dsvars = dsvars['dataset'].str.cat(dsvars['variable'], sep=':')
        output = dsvars.str.cat(sep=';')
        dsvars_str = {"datasets": output}
        return(dsvars_str)

    # Create string specifying dates for request
    def _format_dates(self, dates=None, years=None, months=None, days=None):
        temporal_subset = {}
        if dates is not None:
            if isinstance(dates, list):
                temporal_subset["dates"] = ",".join(dates)
            else:
                temporal_subset["dates"] = dates
        elif years is not None:
            if isinstance(years, list):
                temporal_subset["years"] = ",".join(years)
            else:
                temporal_subset["years"] = years
            if months is not None:
                if isinstance(months, list):
                    temporal_subset["months"] = ",".join(months)
                else:
                    temporal_subset["months"] = months
            if days is not None:
                if isinstance(days, list):
                    temporal_subset["days"] = ",".join(days)
                else:
                    temporal_subset["days"] = days
        return(temporal_subset)

    # Create string representing geometry information for request
    def _format_geometry(self, endpoint, geom):
        spatial_subset = {}
        if geom is None:
            print("No geometry specified")
            return spatial_subset

        # A string geom could be either a guid or a file name
        elif isinstance(geom, str):
            # if geom is a single guid
            if len(geom) == 36 and not "." in geom and "(" not in geom:
                spatial_subset["geom_guid"] = geom
            elif (".zip" in geom or ".shp" in geom or ".geojson" in geom or
                    ".csv" in geom): 
                # assume geom is a filename, attempt to upload
                geom_guid = self.upload_geometry(geom)
                spatial_subset["geom_guid"] = geom_guid

        # Geom is a list of guids
        elif isinstance(geom, list) and \
            all(len(geom[i]) == 36 for i in range(len(geom))):
            guid_list = []
            for i in range(len(geom)):
                guid_list.append(geom[i])
            spatial_subset["geom_guid"] = guid_list

        # Geom is a geodataframe to upload
        elif isinstance(geom, gpd.GeoDataFrame):
            geom_guid = self.upload_geometry(geom)
            spatial_subset["geom_guid"] = geom_guid

        # Geom is a set of clip coordinates in the form of a 2D ndarray
        # or a np.matrix
        elif isinstance(geom, np.ndarray) and geom.ndim == 2 and \
                geom.shape[1] == 2:
            def row_to_string(x):
                out_str = "({},{})".format(*x)
                return out_str
            clip_str = ",".join(
                np.apply_along_axis(row_to_string, axis=1, arr=geom))
            if endpoint == "subset_polygon":
                spatial_subset["clip"] = clip_str
            else:
                spatial_subset["points"] = clip_str

        else: 
            raise Exception("Geometry configuration not implemented")
        return(spatial_subset)

    def _format_temporal_parameters(self, grain_method, validate_method):
        temporal_parameters = {
            "grain_method": grain_method,
            "validate_method": validate_method
        }
        return(temporal_parameters)

    def _format_spatial_parameters(
        self, 
        endpoint, 
        ri_method, 
        t_crs, 
        resolution
    ):
        spatial_parameters = {}
        if endpoint == "subset_points":
            spatial_parameters["interpolation_method"] = ri_method
        else:
            spatial_parameters["resample_method"] = ri_method
        
        if t_crs is not None:
            spatial_parameters["crs"] = str(t_crs)

        if resolution is not None:
            spatial_parameters["resolution"] = str(resolution)

        return spatial_parameters

    def _infer_endpoint(self, geom):
        poly_ep = "subset_polygon"
        pt_ep = "subset_points"

        # If null, then it assumed user wants whole area of datasets
        if geom is None:
            return poly_ep
        elif isinstance(geom, gpd.GeoDataFrame):
            if any(geom.geom_type == "Polygon") or \
            any(geom.geom_type == "MultiPolygon"):
                return poly_ep
            elif any(geom.geom_type == "Point") or \
            any(geom.geom_type == "MultiPoint"):
                return pt_ep
            else:
                raise Exception("Unrecognized geometry type. Could not infer GeoCDL subset endpoint")
        else:
            raise Exception("Unsupported geometry type for inferring GeoCDL subset endpoint. Please use download_[polygon|points]_subset() directly.")

