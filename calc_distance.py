from math import radians, cos, sin, asin, sqrt
def haversine(lng1, lat1, lng2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])
    # haversine formula 
    dlon = lng2 - lng1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371 * c
    mi = km * 0.6213712
    return km
    
from users.database import Database
from jump.models import Sighting, Trip

db = Database('instance/database.sqlite').connect()

sight = Sighting(db)
trip = Trip(db)

recs = trip.select()
for rec in recs:
    s_recs=sight.select(where='id = {} or id = {} '.format(rec.origin_sighting_id, rec.destination_sighting_id))
    if len(s_recs) == 2:
        rec.miles = haversine(s_recs[0].lng,s_recs[0].lat,s_recs[1].lng,s_recs[1].lat)
        trip.save(rec)
        
        
try:
    db.commit()
except:
    db.rollback()
    
db.close()





#while True:
#    lng1 = float(input("Lng 1: "))
#    lat1 = float(input("Lat 1: "))
#    lng2 = float(input("Lng 2: "))
#    lat2 = float(input("lat 2: "))
#
#    print(round(haversine(lng1, lat1, lng2, lat2),3))
#    print() 
    

