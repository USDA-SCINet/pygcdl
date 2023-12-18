import requests
import os
from pathlib import Path
import shutil
import utils
import tempfile

class PyGeoCDL:
    def __init__(self, url_base=None):
        if url_base is None:
            self.url_base='http://127.0.0.1:8000'

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

    def upload_geometry(self, file):
        # This function uploads a user geometry to the GeoCDL
        # REST API and returns a geometry upload ID to use
        # in subset requests.

        if not os.path.isfile(file):
            raise Exception("File not found")

        file_ext = os.path.splitext(file)[1]

        if file_ext == ".geojson" or file_ext == ".zip" or file_ext == ".csv":
            files = {"geom_file": (file, open(file, 'rb'))}
            r = requests.post(self.url_base + '/upload_geom', files=files)
            print(r.text)

            return r.text

        elif file_ext == ".shp":

            # Call utility function to zip all auxillary shapefile files 
            # together
            zip_file_path = str(utils.zip_shapefiles(file))

            files = {"geom_file": (zip_file_path, open(zip_file_path, 'rb'))}
            r = requests.post(self.url_base + '/upload_geom', files=files)
            return r.text
        else:
            raise Exception("File format not yet supported")

    def download_polygon_subset(
        self,
        dsvars,
        dates = None,
        years = None,
        months = None,
        days = None
    ):
        dsvars_string = utils.format_dsvars(dsvars)
        date_string = utils.format_dates(
            dates=dates, years=years, months=months, days = days
        )
        print("dsvars: ", dsvars_string)
        print("dates: ", date_string)
