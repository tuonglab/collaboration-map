# collaboration-map
a simple python script to generate a geographical map of my collaborations based on scival/scopus metrics

## Requirements
```bash
pip install pandas folium geopy pycountry tqdm pycountry-convert
```

## Usage
Create a Researcher collaboration report from SciVal and extract the section detailing the information on institutional collaboration and save as `collab.csv`

In the script, modify the home location to be your coordinates you want e.g. 

```python
home_location = [-27.4975, 153.0137]  # University of Queensland, St Lucia
```

Then just run:
```bash
python map_collab.py
```
