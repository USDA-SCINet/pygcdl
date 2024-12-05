import pygcdl
import pytest
from pytest_httpserver import HTTPServer
import json

# Test list_datasets() call
def test_list_datasets(httpserver: HTTPServer):
    url_base = httpserver.url_for("") # base url
    pygcdl_obj = pygcdl.PyGeoCDL(url_base=url_base)
    dataset_list = [{"id":"ID", "name":"NAME"}]
    httpserver.expect_request(uri="/list_datasets").respond_with_json(dataset_list)
    r = pygcdl_obj.list_datasets()
    assert r == {"ID": "NAME"}

# Test get_dataset_info() call
def test_get_dataset_info(httpserver: HTTPServer):
    url_base = httpserver.url_for("") # base url
    pygcdl_obj = pygcdl.PyGeoCDL(url_base=url_base)
    httpserver.expect_request(uri="/ds_info", query_string="id=PRISM").respond_with_json({"PRISM":"data"})
    r = pygcdl_obj.get_dataset_info("PRISM")
    assert r == {"PRISM":"data"}


