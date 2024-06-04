# pygcdl

Python interface for the Geospatial Common Data Library.

To set up a jupyter notebook kernel for pygcdl on Ceres, run the following commands:

```
module load python_3
python -m venv pygcdl_env
source pygcdl_env/bin/activate
pip install -r requirements.txt
pip install ipykernel
python -m ipykernel install --user --name=pygcdl_env
```
Then, open your jupyter notebook and set your kernel to "pygcdl_env".
