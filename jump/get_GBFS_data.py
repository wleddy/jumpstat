"""Script to fetch and record bike share data using the GBFS system

    ref: https://github.com/NABSA/gbfs/blob/master/gbfs.md
"""

from app import app
import ast
from datetime import datetime, timedelta
from flask import g
import json
from jump.jump_utils import long_time_no_see, miles_traveled
from jump.models import Bike, Sighting, Trip, AvailableBikeCount, init_tables
from mapping.shapes import get_shape_list
import requests
from shapely.geometry import Point, shape
from users.utils import printException


def get_gbfs_data():
    try:
        
        #import pdb;pdb.set_trace()
        
        mes = 'No message Yet...'
        db = g.db
                
        shapes_list = get_shape_list()
        if not shapes_list:
            # most likely the json files don't exist or are in the wrong place
            alert_admin("Error: No shape files were found when trying to get shapes_list in jump.get_data")
    
        # Get free bike status feed url
        url = get_free_bike_url()
        if not url:
            mes = """No Free bike status URL while attempting to import Jump Bike data for {}.
                Time: {}
                URL: {}""".format(app.config['JUMP_NETWORK_NAME'],datetime.now().isoformat(),str(url))
            alert_admin(mes)
            
        request_data = requests.get(url).text
        if "error" in request_data or '"bikes":' not in request_data: # Not sure what an error looks like
            mes = """An error occured while attempting to import Jump Bike data from {}.
                Time: {}
                Error: {}""".format(url,datetime.now().isoformat(),str(request_data))
            alert_admin(mes)
        
            return mes
            
        #convert data from json
        try:
            request_data = json.loads(request_data)
        except:
            # alert on conversion error
            mes = """An error occured while attempting to convert json data.
                Time: {}
                Error: {}""".format(datetime.now().isoformat(),str(request_data))
            alert_admin(mes)
            
            return mes
        
        #Are there any bikes?
        if not request_data['data']['bikes']:
            mes = """No bikes were retrievd.
                Time: {}
                Error: {}""".format(datetime.now().isoformat(),str(request_data))
            alert_admin(mes)
            
            return mes
            
        #got data!
        observations = request_data['data']['bikes']
        
        retrieval_dt = datetime.now()
        sightings = Sighting(db)
        bikes = Bike(db)
        trips = Trip(db)
        new_data = {'sighting':0, 'bike': 0, 'trip': 0, 'available': 0,}
        avail_city_data = {}
    
        for ob in observations:
            
            lng = ob['lon']
            lat = ob['lat']
            ob['retrieved'] = retrieval_dt

            # the bike_id for jump is prepended with 'bike_' so we need to strip that off
            bike_id = ob.get('bike_id',None)
            if not bike_id:
                mes = """bike_id not in data.
                    Time: {}""".format(datetime.now().isoformat(),)
                alert_admin(mes)
                continue
                
            pos = ob['bike_id'].find('_')
            if pos > 0:
                ob['bike_id'] = ob['bike_id'][pos+1:]
                
            # jump has a custom field 'jump_ebike_battery_level' with a '%' sign. Drop the sign
            batt_pct = ob.get('jump_ebike_battery_level',None)
            if batt_pct:
                pos = batt_pct.find("%")
                if pos > 0:
                    ob['jump_ebike_battery_level'] = batt_pct[:pos]
  
            sql = 'jump_bike_id = {}'.format(ob['bike_id'])
            bike = bikes.select_one(where=sql)
            new_data['available'] += 1
            
            city = get_city(lng,lat,shapes_list)
            if city in avail_city_data:
                avail_city_data[city] += 1
            else:
                avail_city_data[city] = 1
            
            if not bike:
                # A new bike...
                bike = bikes.new()
                bike.jump_bike_id = ob['bike_id']
                bike.name = ob.get('name',None)
                bikes.save(bike)
                new_data['bike'] += 1
                sightings.save(new_sighting(sightings,ob,shapes_list))
                new_data['sighting'] += 1
                
                # no need to look for previous sightings
                continue
            
            #Get the last time we saw this bike
            where = 'jump_bike_id = {}'.format(bike.jump_bike_id)
            order_by = 'id desc' # should be by datetime, but there are issues

            sight = sightings.select_one(where=where, order_by=order_by)
            if not sight:
                #This should really never happen...
                sightings.save(new_sighting(sightings,ob,shapes_list))
                new_data['sighting'] += 1
                continue
                
            if long_time_no_see(datetime.strptime(sight.retrieved,'%Y-%m-%d %H:%M:%S.%f')):
                #This bike has been off getting service
                sight = new_sighting(sightings,ob,shapes_list,returned_to_service=1)
                sightings.save(sight)
                #print('Returned to service: {}'.format(sight))
                new_data['sighting'] += 1
                continue
                
            # Seeing the bike again so how far has it moved
            distance = miles_traveled(lng, lat, sight.lng, sight.lat)
            if distance >= 0.128:
                #import pdb;pdb.set_trace()
                #bike moved at least 1/8 mile
                origin_id = sight.id
                sight = new_sighting(sightings,ob,shapes_list)
                sightings.save(sight)
                #print('New Trip Sighting: {}'.format(sight))
                
                new_data['sighting'] += 1
                # Make a trip
                trip = new_trip(trips,bike.jump_bike_id,origin_id,sight.id,distance)
                trips.save(trip)
                #print('New Trip : {}'.format(sight))
                new_data['trip'] += 1
                
            else:
                #too short a move, Just update the sighting record
                sightings.save(update_sighting(ob,sight))
                
        #end ob loop
        
        # record the number of available bikes
        if new_data['available'] > 0:
            for city in avail_city_data.keys():
                avail = AvailableBikeCount(db).new()
                avail.bikes_available = avail_city_data[city]
                avail.city = city
                avail.retrieved = retrieval_dt
                avail.day_number = day_number()
                AvailableBikeCount(db).save(avail)
        
        db.commit()
        mes = 'At {}; New Data added: Available: {}, Sightings: {}, Bikes: {}, Trips: {}'.format(datetime.now().isoformat(),new_data['available'],new_data['sighting'],new_data['bike'],new_data['trip'])
        
        return(mes)
    
    except Exception as e:
        mes = """An error occured while attempting to fetch bike data.
                Error: {}
                """.format(str(e))
        mes = printException(mes,"error",e)
        alert_admin(mes)
        return mes
            

def alert_admin(mes):
    with app.app_context():
        from users.mailer import send_message
        # send an email to admin
        sent,msg = send_message(
            None,
            subject="Error Getting Jump Data at {}".format(app.config['HOST_NAME'],),
            body = mes,
            )

    
def new_sighting(sightings,data,shapes_list,**kwargs):
    """
    Create a new sighting record object and return it.
    data is single row of the Jump Bike response object
    
    """
    
    returned_to_service = kwargs.get('returned_to_service',0)
    
    rec = sightings.new()
    rec.jump_bike_id = data.get('bike_id',None)
    rec.bike_name = data.get('name',None)
    rec.retrieved = data.get('retrieved',datetime.now())
    rec.sighted = rec.retrieved
    #rec.address = data.get('address',None)
    rec.network_id = data.get(app.config['JUMP_NETWORK_NAME'],None)
    rec.lng = data.get('lon',None)
    rec.lat = data.get('lat',None)
    rec.returned_to_service = returned_to_service
    rec.city = get_city(rec.lng,rec.lat,shapes_list)
    rec.batt_level = data.get('jump_ebike_battery_level',None)
    #rec.batt_distance = data.get('ebike_battery_distance',None)
    #rec.hub_id = data.get('hub_id',None)
    rec.day_number = day_number()
    
    ## Get the bonuses
    #rec.bonuses = get_bonuses(data.get('bonuses',None),rec)
    return rec
    
def update_sighting(data,sight):
    """
    Update the sighting record with the latest data
    """
    sight.retrieved = data.get('retrieved',datetime.now())
    sight.day_number = day_number()
    ## Don't think I want to update the batt level between new sightings
    #sight.batt_level = data.get('batt_level',None)
    #sight.batt_distance = data.get('batt_distance',None)
    #sight.bonuses = get_bonuses(data.get('bonuses',sight.bonuses),sight)
    
    return sight
    
def new_trip(trips,bike_id,origin_id,destination_id,distance):
    """
    Create a new trip record
    """
    trip = trips.new()
    trip.jump_bike_id = bike_id
    trip.origin_sighting_id = origin_id
    trip.destination_sighting_id = destination_id
    trip.miles = distance
    
    return trip
    
def day_number():
    return int(datetime.now().strftime('%Y%m%d'))
    
def get_city(lng,lat,shapes_list=None):
    """
    Return the name of the city where we found this bike
    
    9/3/18 - Now use mapping.shapes.get_shape_list to provide
    a list of dictionaries with shapely shape objects to test 
    to see if the bike is in there
    
    10/1/18 - If city can't be found in shape files, try reverse geocode lookup
    
    """
    city = None
    
    if shapes_list:
        point = Point(lng,lat) # longitude, latitude
        for city_dict in shapes_list:
            if shape(city_dict['shape']).contains(point):
                city = city_dict['city_name']
                break
            
    if not city:
        #attempt geocode lookup
        url = "https://nominatim.openstreetmap.org/reverse?format=json&lat={}&lon={}&zoom=18&addressdetails=1".format(lat,lng,)
        try:
            geo_data = requests.get(url).text
            #convert data from json
            geo_data = json.loads(geo_data)
            #look in address:{..., "city":'XXXXXX',...}
            add = geo_data.get('address',None)
            city = add.get('city',None)
            if not city:
                #Not technically in the city?
                city = add.get('county',None)
        except:
            # alert on conversion error
            mes = """An error occured while attempting to convert json data.
                URL: {}
                Time: {}
                Data: {}""".format(url,datetime.now().isoformat(),str(geo_data))
            alert_admin(mes)

    if not city:
        city = "Unknown"
    return city
    
    
def get_free_bike_url():
    """get the url to the free bike list based on the site JUMP_GBFS_ROOT_URL from app.config"""
        
    url = app.config['JUMP_GBFS_ROOT_URL']
    request_data = requests.get(url).text
    if "error" in request_data or '"feeds":' not in request_data: # Not sure what an error looks like
        mes = """An error occured while attempting to import Jump Bike feed from {}.
            Time: {}
            Error: {}""".format(url,datetime.now().isoformat(),str(request_data))
        alert_admin(mes)
    
        return None
        
    #convert data from json
    try:
        request_data = json.loads(request_data)
    except:
        # alert on conversion error
        mes = """An error occured while attempting to convert json data.
            Time: {}
            Error: {}""".format(datetime.now().isoformat(),str(request_data))
        alert_admin(mes)
        
        return None
    
    #Find the free bike url
    url = None
    for item in request_data['data']['en']['feeds']:
        if item.get('name',None) == 'free_bike_status':
            url = item.get('url',None)
            break
            
    if url:
        return url
    else:
        mes = """No valid feeds were retrievd.
            Time: {}
            Error: {}""".format(datetime.now().isoformat(),str(request_data))
        alert_admin(mes)
        
        return None
    
    
    
# Bonus data not include in current feed
def get_bonuses(bonuses,sight):
    """
    Return a string version of the bonuses JSON object or None
    
    bonuses is the bonuses element of the Jump Bike response
    sight is a namedList object of the current sighting record
    """

    if type(bonuses) is list:
        try:
            #convert a string to a list of dicts
            bonus_list = ast.literal_eval(sight.bonuses)
        except ValueError:
            # probably None
            bonus_list = []

        for bonus_dict in bonuses:
            if bonus_dict and len(bonus_list) > 0:
                for prev_bonus in bonus_list:
                    if 'type' in prev_bonus and 'type' in bonus_dict and \
                    prev_bonus['type'] == bonus_dict['type']:
                        #Leave previous bonus as it is
                        bonus_dict = None
                       
            if bonus_dict: 
                #convert the date to a string
                bonus_dict['retrieved'] = sight.retrieved.strftime('%Y-%m-%d %H:%M:%S')
                bonus_list.append(bonus_dict)
                       
        if len(bonus_list) > 0: 
            return str(bonus_list)
    else:
        return sight.bonuses #leave it unchanged
    
    return None
