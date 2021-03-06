import sys
import os
sys.path.append('') ##get import to look in the working dir.
working_path = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.append(working_path) ##get import to look one level up

import requests
import json
from datetime import datetime, timedelta
from takeabeltof.date_utils import local_datetime_now
from app import app
from jump.models import Bike, Sighting, Trip, AvailableBikeCount, init_tables
from jump.jump_utils import long_time_no_see, miles_traveled
from takeabeltof.utils import printException
import ast
from shapely.geometry import Point, shape
from mapping.shapes import get_shape_list

# Sample request data:
# {
#     "current_page": 1,
#     "per_page": 1000,
#     "total_entries": 336,
#     "items": [
#         {
#             "id": 21096,
#             "name": "1247",
#             "network_id": 165,
#             "sponsored": false,
#             "ebike_battery_level": 52,
#             "ebike_battery_distance": 19.76,
#             "hub_id": null,
#             "inside_area": true,
#             "address": "1230 J Street, Sacramento",
#             "current_position": {
#                 "type": "Point",
#                 "coordinates": [
#                     -121.49046166666666,
#                     38.579485
#                 ]
#             },
#             "bonuses": [
#  only if a bonus exists --> {'type': 'bringing_discharged_ebike_to_charging_station', 'amount': 0.5}
#             ]
#         },
#         {
# ]}
################################

def run():
    """Fetch and compile data from Jump"""
    print(get_jump_data())

def get_jump_data():
    try:
        mes = 'No message Yet...'
        from takeabeltof.database import Database
        db = Database(working_path + "/" + app.config['DATABASE_PATH']).connect()
        init_tables(db) # creates tables if needed

    
        # Use this to determine if bikes have been off the system too long (getting recharged?)
        
        last_sighting_limit = (local_datetime_now() - timedelta(hours=2)).isoformat(sep=' ')

        #size=10
        #network = 165
        size = app.config['JUMP_REQUEST_SIZE']
        network = app.config['JUMP_NETWORK_ID']
        shapes_list = get_shape_list()
        if not shapes_list:
            # most likely the json files don't exist or are in the wrong place
            alert_admin("Error: No shape files were found when trying to get shapes_list in jump.get_data")
        # I now have 2 Jump accounts to use for polling the server, so I can poll more often
        # if the minutes are odd, or even...
    
        if (local_datetime_now().minute % 2 == 0): #even 
            row = 0
        else: #odd
            row = 1
        
        username = app.config['JUMP_LOGIN'][row][0]
        password = app.config['JUMP_LOGIN'][row][1]
    
        url = 'https://app.socialbicycles.com/api/bikes.json?page=1&per_page={}&network_id={}'.format(size,network)
        request_data = requests.get(url,auth=(username,password)).json()
        if "error" in request_data or 'items' not in request_data: # {"error":"Not Authenticated","code":401}
            db.close()
            mes = """An error occured while attempting to import Jump Bike data.
                Time: {}
                Error: {}""".format(local_datetime_now().isoformat(),str(request_data))
            alert_admin(mes)
        
            return "Error received while accessing Jump Data: {}".format(str(request_data))
    
        observations = request_data['items']
        
        retrieval_dt = local_datetime_now()
        sightings = Sighting(db)
        bikes = Bike(db)
        trips = Trip(db)
        new_data = {'sighting':0, 'bike': 0, 'trip': 0, 'available': 0,}
        avail_city_data = {}
    
        for ob in observations:        
            lng = ob['lng'] = ob['current_position']['coordinates'][0]
            lat = ob['lat'] = ob['current_position']['coordinates'][1]
            ob['retrieved'] = retrieval_dt

            sql = 'jump_bike_id = {}'.format(ob['id'])
            bike = bikes.select_one(where=sql)
            new_data['available'] += 1
            
            city = get_city(shapes_list,lng,lat)
            if city in avail_city_data:
                avail_city_data[city] += 1
            else:
                avail_city_data[city] = 1
            
            if not bike:
                # A new bike...
                bike = bikes.new()
                bike.jump_bike_id = ob.get('id',None)
                bike.name = ob.get('name',None)
                bikes.save(bike)
                new_data['bike'] += 1
                sightings.save(new_sighting(sightings,ob,shapes_list))
                new_data['sighting'] += 1
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
        mes = 'At {}; New Data added: Available: {}, Sightings: {}, Bikes: {}, Trips: {}'.format(local_datetime_now().isoformat(),new_data['available'],new_data['sighting'],new_data['bike'],new_data['trip'])
        
        return(mes)
    
    except Exception as e:
        try:
            if db:
                db.rollback()
        except Exception as e:
            mes = """Could not connect to db while attempting to import Jump Bike data.
                    Error: {}
                    """.format(str(e))
            mes = printException(mes,"error",e)
            alert_admin(mes)
            return mes
            
            
        mes = """An error occured while attempting to import Jump Bike data.
                Error: {}
                """.format(str(e))
        mes = printException(mes,"error",e)
                
        alert_admin(mes)
        return mes
        
def alert_admin(mes):
    with app.app_context():
        from takeabeltof.mailer import send_message
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
    rec.jump_bike_id = data.get('id',None)
    rec.bike_name = data.get('name',None)
    rec.retrieved = data.get('retrieved',local_datetime_now())
    rec.sighted = rec.retrieved
    rec.address = data.get('address',None)
    rec.network_id = data.get('network_id',None)
    rec.lng = data.get('lng',None)
    rec.lat = data.get('lat',None)
    rec.returned_to_service = returned_to_service
    rec.city = get_city(shapes_list,rec.lng,rec.lat)
    rec.batt_level = data.get('ebike_battery_level',None)
    rec.batt_distance = data.get('ebike_battery_distance',None)
    rec.hub_id = data.get('hub_id',None)
    rec.day_number = day_number()
    
    ## Get the bonuses
    rec.bonuses = get_bonuses(data.get('bonuses',None),rec)
    return rec
    
def update_sighting(data,sight):
    """
    Update the sighting record with the latest data
    """
    sight.retrieved = data.get('retrieved',local_datetime_now())
    sight.day_number = day_number()
    ## Don't think I want to update the batt level between new sightings
    #sight.batt_level = data.get('batt_level',None)
    #sight.batt_distance = data.get('batt_distance',None)
    sight.bonuses = get_bonuses(data.get('bonuses',sight.bonuses),sight)
    
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
    return int(local_datetime_now().strftime('%Y%m%d'))
    
def get_city(shapes_list,lng,lat):
    """
    Return the name of the city where we found this bike
    
    9/3/18 - Now use mapping.shapes.get_shape_list to provide
    a list of dictionaries with shapely shape objects to test 
    to see if the bike is in there
    
    """
    city = "Unknown"
    point = Point(lng,lat) # longitude, latitude
    for city_dict in shapes_list:
        if shape(city_dict['shape']).contains(point):
            city = city_dict['city_name']
            break
            
    return city
    
    
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
    
    
    
if __name__ == '__main__':
    run()


    
