# pygcdl

Python interface for the Geospatial Common Data Library.

To set up a jupyter notebook kernel for pygcdl on Ceres, run the following commands:

module load python_3 </br>
python -m venv pygcdl_env </br>
source pygcdl_env/bin/activate </br>
pip install -r requirements.txt </br>
pip install ipykernel </br>
python -m ipykernel install --user --name=pygcdl_env </br>

Then, open your jupyter notebook and set your kernel to "pygcdl_env".
