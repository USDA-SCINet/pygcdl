import requests

class PyGeoCDL:
	def __init__(self, url_base=None):
		if url_base is None:
			self.url_base='http://127.0.0.1:8000'

	def getDatasets(self):
		"""
		Retrieves the ID and name of all available GeoCDL datasets. The
		dataset information is returned as a dictionary in which the dataset
		IDs are the keys and the dataset names are the values.
		"""
		r = requests.get(self.url_base + '/list_datasets')

		return {val['id']: val['name'] for val in r.json()}

	def getDatasetInfo(self, dsid):
		"""
		Returns all metadata for the dataset with the given dataset ID. The
		metadata are returned as a dictionary of key: value pairs.
		"""

		r = requests.get(self.url_base + '/ds_info', params={'id': dsid})

		return r.json()

	def uploadGeom(self, file):
		files = {"file": (file, open(file, 'rb'), 'application/json', {'Expires': '0'})}
		r = requests.post(self.url_base + '/upload_geom', files=files)
		return r.text