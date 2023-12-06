import requests
import os
from pathlib import Path
import shutil

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

	def view_metadata(self, dsid):
		"""
		Returns all metadata for the dataset with the given dataset ID. The
		metadata are returned as a dictionary of key: value pairs.
		"""

		r = requests.get(self.url_base + '/ds_info', params={'id': dsid})

		return r.json()

	def upload_geometry(self, file):
		if not os.path.isfile(file):
			raise Exception("File not found")
		file_ext = os.path.splitext(file)[1]
		if file_ext == ".geojson" or file_ext == ".zip" or file_ext == ".csv":
			files = {"geom_file": (file, open(file, 'rb'))}
			#headers = {'Content-type': 'multipart/form-data; charset=UTF-8'}
			r = requests.post(self.url_base + '/upload_geom', files=files)
			print(r.text)
			return r.text
		elif file_ext == ".shp":
			#grab auxiliary files: dbf, shx, prj
			shp_file_path = os.path.abspath(file) #ie /dir/to/file_name.shp
			base_data_dir = os.path.dirname(os.path.abspath(file))
			base_file_path = os.path.splitext(shp_file_path)[0] #ie /dir/to/file_name
			base_file_name = os.path.splitext(os.path.basename(shp_file_path))[0] #ie file_name
			dbf_file_path = base_file_path + ".dbf"
			if not os.path.isfile(dbf_file_path):
				raise Exception("Insufficient auxiliary shapefile files")
			shx_file_path = base_file_path + ".shx"
			if not os.path.isfile(shp_file_path):
				raise Exception("Insufficient auxiliary shapefile files")
			prj_file_path = base_file_path + ".prj"
			if not os.path.isfile(prj_file_path):
				raise Exception("Insufficient auxiliary shapefile files")
			#Create a new folder for shapefiles to be zipped in
			new_data_dir = os.path.abspath(os.path.join(base_data_dir, base_file_name))
			os.mkdir(new_data_dir)
			#copy shp file	
			base_shp_file_name = os.path.basename(file)
			shutil.copyfile(file, os.path.join(new_data_dir, base_shp_file_name))
			#copy dbf file
			base_dbf_file_name = os.path.basename(dbf_file_path)
			shutil.copyfile(file, os.path.join(new_data_dir, base_dbf_file_name))
			#copy shx file
			base_shx_file_name = os.path.basename(shx_file_path)
			shutil.copyfile(file, os.path.join(new_data_dir, base_shx_file_name))
			#copy prj file
			base_prj_file_name = os.path.basename(prj_file_path)
			shutil.copyfile(file, os.path.join(new_data_dir, base_prj_file_name))
			shutil.make_archive(base_dir = new_data_dir, root_dir = base_file_path, format = 'zip', base_name = base_file_name)
			zip_file_name = base_file_name + ".zip"
			zip_file_path = os.path.join(base_data_dir, zip_file_name)
			files = {"geom_file": (zip_file_path, open(zip_file_path, 'rb'))}
			r = requests.post(self.url_base + '/upload_geom', files=files)
			shutil.rmtree(new_data_dir)
			print(r.text)
			return r.text
		else:
			raise Exception("File format not yet supported")
		