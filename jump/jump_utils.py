"""
Some utility functions for jump
"""

from datetime import datetime, timedelta
from date_utils import local_datetime_now
from math import radians, cos, sin, asin, sqrt

def long_time_no_see(previous_date,newer_date=None):
    """
    Return True if it has been over the time limit since we last saw this bike
    else False
    """
    if newer_date == None:
        newer_date = local_datetime_now()
        
    if previous_date <= newer_date - timedelta(hours=2):
        #it's been a while
        return True

    return False


def miles_traveled(lng1, lat1, lng2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    if lng1 == None or lng2 == None or lat1 == None or lat2 == None:
        return 0
    
    # convert decimal degrees to radians 
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    # haversine formula 
    dlon = lng2 - lng1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371 * c

    mi = km * 0.6213712 #convert to miles
    return mi


