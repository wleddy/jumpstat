import sys
import os
sys.path.append('') ##get import to look in the working dir.
working_path = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.append(working_path) ##get import to look one level up

import requests
import json
from datetime import datetime
from app import app
from jump.models import Bike, Sighting, Trip, init_tables

db = None

from users.database import Database
db = Database(working_path + "/" + app.config['DATABASE_PATH']).connect()
init_tables(db) # creates tables if needed


###############################
# Use the lng to determine what city the bike is in.
# Sac, west Sac boundry -121.507909
# Davis, West Sac Boundery -121.618708
eastern_davis_boundry = -121.618708
eastern_west_sac_boundry = -121.507909

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
# 
#             ]
#         },
#         {
# ]}
################################

def run():
    """Fetch and compile data from Jump"""
    get_jump_data()

def get_jump_data():
    new_data = {'sighting':0, 'bike': 0, 'trip': 0}
    #size=10
    #network = 165
    size = app.config['JUMP_REQUEST_SIZE']
    network = app.config['JUMP_NETWORK_ID']
    url = 'https://app.socialbicycles.com/api/bikes.json?page=1&per_page={}&network_id={}'.format(size,network)
    username = app.config['JUMP_USERNAME']
    password = app.config['JUMP_PASSWORD']
    
    observations = requests.get(url,auth=(username,password)).json()['items']
    
    retrieval_dt = datetime.now()
    day_number = int(retrieval_dt.strftime('%Y%m%d'))
    sighting = Sighting(db)
    bike = Bike(db)
    trip = Trip(db)
    
    for ob in observations:        
        new_sighting = False
        sql = 'bike_id = {} and lng = {} and lat = {}'.format(ob['id'],ob['current_position']['coordinates'][0],ob['current_position']['coordinates'][1])
        sight = sighting.select_one(where=sql)
        if sight != None:
            # update the sighting date
            sight.retrieved = retrieval_dt
            sighting.save(sight)
        else:
            # only create a record if the bike has moved
            new_sighting = True
            sight = sighting.new()
            sight.bike_id = ob['id']
            sight.bike_name = ob['name']
            sight.retrieved = retrieval_dt
            sight.address = ob['address']
            sight.network_id = ob['network_id']
            sight.lng = ob['current_position']['coordinates'][0]
            sight.lat = ob['current_position']['coordinates'][1]
            if sight.lng <= eastern_davis_boundry:
                sight.city = "Davis"
            elif sight.lng <= eastern_west_sac_boundry:
                sight.city = "West Sacramento"
            else:
                sight.city = "Sacramento"
                
            sight.batt_level = ob['ebike_battery_level']
            sight.batt_distance = ob['ebike_battery_distance']
            sight.hub_id = ob['hub_id']
            sight.day_number = day_number
            sighting.save(sight)
            new_data['sighting'] += 1
            
        #add a bike?
        bk = bike.select_one(where='bike_id = {}'.format(ob['id']))
        if bk == None:
            bk = bike.new()
            bk.bike_id = ob['id']
            bk.name = ob['name']
            bike.save(bk)
            new_data['bike'] += 1
            
        if new_sighting:
            # record the trip that got us to this location
            ### If we get 2 or more sightings for this bike we can record a trip
            temp_sight = sighting.select(where='bike_id = {}'.format( ob['id']), order_by='retrieved desc')
            #import pdb;pdb.set_trace()
            if temp_sight and len(temp_sight) >= 2:
                trp = trip.new()
                trp.bike_id = sight.bike_id
                trp.prev_sighting_id = temp_sight[1].id
                trp.next_sighting_id = temp_sight[0].id
                try:
                    trip.save(trp)
                    new_data['trip'] += 1
                    
                except Exception as e:
                    print(trp)
                    print(e)
        
    try:
        db.commit()
        print('New Data added: Sightings: {}, Bikes: {}, Trips: {}'.format(new_data['sighting'],new_data['bike'],new_data['trip']))
    except Exception as e:
        db.rollback()
        print(e)


if __name__ == '__main__':
    run()


    
