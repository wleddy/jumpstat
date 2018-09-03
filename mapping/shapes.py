from app import app
from shapely.geometry import Point, shape
import json
import os

def get_shape_list(path=None):
    """
    Return a list of dictionaries containing shapely objects. 
    Use json files for polygons 
    
    If the path is specified it must be an absolute path to the directory to search
    
    """
    
    if path == None:
        path = os.path.dirname(os.path.abspath(__file__)) + "/json/" + app.config['JUMP_NETWORK_NAME'] + '/'
    
    shape_list = []
    #look in the source path for any json files and process each one
    #import pdb;pdb.set_trace()
    if os.path.exists(path):
        file_list = os.listdir(path)
        file_list.sort()
    
        for filename in file_list:
            filepath = path+filename
            base, file_extension = os.path.splitext(filepath)
            if file_extension == '.json':
                f = open(filepath)
                j = json.loads(f.read())
                f.close()
                out = {}
                out['city_name'] = j['city_name'] # Make this easy to get to
                out['shape'] = shape(j)
                shape_list.append(out)
    

    return shape_list
    