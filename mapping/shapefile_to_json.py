import fiona
from shapely.geometry import asShape, Point, mapping
import json
import argparse
import os 


parser = argparse.ArgumentParser()
parser.add_argument('in_filespec', help='source file path')
parser.add_argument('city_name', help='The name of the city')
parser.add_argument('--out_filespec', help='desination directory path', default='mapping/json/')
args = parser.parse_args()
in_filespec = args.in_filespec
out_filespec = args.out_filespec
city_name = args.city_name

if not os.path.exists(os.path.dirname(out_filespec)):
    os.makedirs(out_filespec)

with fiona.open(in_filespec) as fiona_collection:

    # In this case, we'll assume the shapefile only has one record/layer (e.g., the shapefile
    # is just for the borders of a single country, etc.).
    shapefile_record = fiona_collection.next()

    # Use Shapely to create the polygon
    shape = asShape( shapefile_record['geometry'] )
    j = json.dumps(mapping(shape))
    j = json.loads(j) #Convert it to a dictionary
    j['city_name'] = city_name
    out_filespec = "{}/{}.json".format(out_filespec,city_name.lower().replace(" ","_"))
    j = json.dumps(j) #convert it back to a string
    f = open(out_filespec,mode='w')
    f.write(j)
    f.close()
    print(j)
        