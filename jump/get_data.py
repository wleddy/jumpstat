import sys
import os
sys.path.append('') ##get import to look in the working dir.
working_path = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.append(working_path) ##get import to look one level up

import requests
import json
from datetime import datetime
from app import app
from jump.models import Bike, Sighting, Trip, AvailableBikeCount, init_tables

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
    print(get_jump_data())

def get_jump_data():
    try:
        from users.database import Database
        db = Database(working_path + "/" + app.config['DATABASE_PATH']).connect()
        init_tables(db) # creates tables if needed

        ###############################
        # Use the lng to determine what city the bike is in.
        # Crude but simple
        eastern_davis_boundry = -121.618708 # Davis, West Sac Boundery
        eastern_west_sac_boundry = -121.507909 # Sac, west Sac boundry
    
        # Use this to determine if bikes have been off the system too long (getting recharged?)
        last_sighting_limit = datetime.now().replace(hour=datetime.now().hour-2).isoformat(sep=' ')
    
        #size=10
        #network = 165
        size = app.config['JUMP_REQUEST_SIZE']
        network = app.config['JUMP_NETWORK_ID']
    
        # I now have 2 Jump accounts to use for polling the server, so I can poll more often
        # if the minutes are odd, or even...
    
        if (datetime.now().minute % 2 == 0): #even 
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
                Error: {}""".format(datetime.now().isoformat(),str(request_data))
            alert_admin(mes)
        
            return "Error received while accessing Jump Data: {}".format(str(request_data))
    
        observations = request_data['items']
        
        retrieval_dt = datetime.now()
        day_number = int(retrieval_dt.strftime('%Y%m%d'))
        sighting = Sighting(db)
        bike = Bike(db)
        trip = Trip(db)
        new_data = {'sighting':0, 'bike': 0, 'trip': 0, 'available': 0,}
        avail_city_data = {}
    
        for ob in observations:        
            new_sighting = False
            sql = 'jump_bike_id = {} and lng = {} and lat = {}'.format(ob['id'],ob['current_position']['coordinates'][0],ob['current_position']['coordinates'][1])
            sight = sighting.select_one(where=sql)
            new_data['available'] += 1
        
            #determine the city for this sighting
            lng = ob['current_position']['coordinates'][0]
            lat = ob['current_position']['coordinates'][1]
            if lng <= eastern_davis_boundry:
                city = "Davis"
            elif lng <= eastern_west_sac_boundry:
                city = "West Sacramento"
            else:
                city = "Sacramento"
            if city in avail_city_data:
                avail_city_data[city] += 1
            else:
                avail_city_data[city] = 1
            
            if sight != None:
                # update the sighting date
                sight.retrieved = retrieval_dt
                sight.day_number = day_number
                sighting.save(sight)
            else:
                # only create a record if the bike has moved
                new_sighting = True
                sight = sighting.new()
                sight.jump_bike_id = ob.get('id',None)
                sight.bike_name = ob.get('name',None)
                sight.retrieved = retrieval_dt
                sight.address = ob.get('address',None)
                sight.network_id = ob.get('network_id',None)
                sight.lng = lng
                sight.lat = lat
                sight.city = city
                
                sight.batt_level = ob.get('ebike_battery_level',None)
                sight.batt_distance = ob.get('ebike_battery_distance',None)
                sight.hub_id = ob.get('hub_id',None)
                sight.day_number = day_number
                sighting.save(sight)
                new_data['sighting'] += 1
            
            #add a bike?
            bk = bike.select_one(where='jump_bike_id = {}'.format(ob.get('id',None)))
            if bk == None:
                bk = bike.new()
                bk.jump_bike_id = ob.get('id',None)
                bk.name = ob.get('name',None)
                bike.save(bk)
                new_data['bike'] += 1
            
            if new_sighting:
                # record the trip that got us to this location
                """
                    If we have seen this sighting before AND it was within the last 2 hours
                    just update the sighting date.
                    Otherwise we will assume that this bike has been off somewhere getting
                    Charged / repaired / or possibly redistributed.
                    I don't know how long a bike will be off line during redisribution. It could
                    happen quicker than 2 hours but I suspect they would just drop a recharged bike
                    where it's needed and any "excess" bikes with low charge would go back for recharge
                
                    If a we determine that a bike has re-appeared on the net after being serviceed, 
                    mark 'returned_to_service' as i in the just created sighting record
                """
                # last_sighting_limit = datetime.now().replace(hour=datetime.now().hour-2).isoformat(sep=' ')
            
                ### If we get 2 or more sightings for this bike we can record a trip and
                ### it was NOT over the time limit, record a new trip
                temp_sight = sighting.select(where='jump_bike_id = {}'.format( ob.get('id',None)), order_by='retrieved desc')
                if temp_sight and len(temp_sight) >= 2:
                    if temp_sight[1].retrieved > last_sighting_limit:
                        trp = trip.new()
                        trp.jump_bike_id = sight.jump_bike_id
                        trp.origin_sighting_id = temp_sight[1].id
                        trp.destination_sighting_id = temp_sight[0].id

                        trip.save(trp)
                        new_data['trip'] += 1
                         
                    else:
                        # Update the service data for the newly created sighting
                        #import pdb;pdb.set_trace()
                        sight.returned_to_service = 1
                        sighting.save(sight)
                    
        # record the number of available bikes
        if new_data['available'] > 0:
            for city in avail_city_data.keys():
                avail = AvailableBikeCount(db).new()
                avail.bikes_available = avail_city_data[city]
                avail.city = city
                avail.retrieved = retrieval_dt
                avail.day_number = day_number
                AvailableBikeCount(db).save(avail)
        
        db.commit()
        mes = 'At {}; New Data added: Available: {}, Sightings: {}, Bikes: {}, Trips: {}'.format(datetime.now().isoformat(),new_data['available'],new_data['sighting'],new_data['bike'],new_data['trip'])
        #print(mes)
        return(mes)
    
    except Exception as e:
        if db:
            db.rollback()
        mes = """An error occured while attempting to import Jump Bike data.
                Time: {}
                Error: {}""".format(datetime.now().isoformat(),str(e))
        alert_admin(mes)
        return mes
        
def alert_admin(mes):
    with app.app_context():
        from users.mailer import send_message
        # send an email to admin
        sent,msg = send_message(
            None,
            subject="Error Getting Jump Data",
            body = mes,
            )


if __name__ == '__main__':
    run()


    
