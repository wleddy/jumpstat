import fiona
from shapely.geometry import asShape, Point, mapping
import json
import argparse
import os 


parser = argparse.ArgumentParser()
parser.add_argument('in_filespec', help='source file path')
parser.add_argument('city_name', help='The name of the city')
parser.add_argument('-o','--outpath', help='desination directory path, defaults to mapping/json/', default='mapping/json/')
args = parser.parse_args()
in_filespec = args.in_filespec
outpath = args.outpath
city_name = args.city_name

if not os.path.exists(os.path.dirname(outpath)):
    os.makedirs(outpath)

with fiona.open(in_filespec) as fiona_collection:

    shapefile_record = fiona_collection.next()

    # Use Shapely to create the polygon
    shape = asShape( shapefile_record['geometry'] )
    shape_dict = mapping(shape)
    shape_dict['city_name'] = city_name
    out_filespec = "{}/{}.json".format(outpath,city_name.lower().replace(" ","_"))
    j = json.dumps(shape_dict) #convert it  a string
    f = open(out_filespec,mode='w')
    f.write(j)
    f.close()
    print(j)
        