##Notes on mapping

I'm attempting a really simple approach to using information from shapefiles to determine the city in which a 
bike is located.

I used an online service at [https://gis.ucla.edu/apps/click2shp/](https://gis.ucla.edu/apps/click2shp/) to create
very simple polygons of the city regions as I define them for my purposes.

The script `shapefile_to_json.py` reads the .shp files created by the service and renders them as json text files.

`shapefile_to_json.py` uses the `fiona` module to import the .shp file and `shapely` to convert it to json text

The usage of the script is: 
    `python shapefile_to_json.py <path to shp file> <city name> <output directory :defaults to mapping/json/>`

When the data is needed the shapely module is used to convert the json data to a shape that can be tested for the
existance of a point.

