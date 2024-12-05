# USDA-ARS Geospatial Common Data Library (GeoCDL) - python package

The pygcdl package is an optional interface for the GeoCDL web API running on the 
SCINet Ceres cluster. 
Please see 
[https://github.com/USDA-SCINet/gcdl](https://github.com/USDA-SCINet/gcdl) 
for the web API itself.

## Getting started

To set up a jupyter notebook kernel for pygcdl on Ceres, run the following commands:

```
module load python_3 </br>
python -m venv pygcdl_env </br>
source pygcdl_env/bin/activate </br>
pip install -r requirements.txt </br>
pip install ipykernel </br>
python -m ipykernel install --user --name=pygcdl_env </br>
```
Then, open your jupyter notebook and set your kernel to "pygcdl_env".

To get started with pygcdl, go through the pygcdl_tutorial.ipynb tutorial.
