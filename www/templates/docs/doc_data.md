## Data Dictionary

The Data dictionary for jumpstat as of Aug. 20, 2018:

* **Bike** Table
    * **id** INT:
    * **jump_bike_id** NUMBER: Jump Bike's internal id
    * **name** TEXT: The number displayed on the bike as reported by the API

 
* **Sighting** Table  
The location information returned by the API plus some we add
    * **id** INT
    * **jump_bike_id** NUMBER: Jump Bike's internal id
    * **bike_name** TEXT: The number displayed on the bike as reported by the API
    * **retrieved** DATETIME: The datetime when we received the data.  
        * This value is updated as long as the bike stays in it's current location
    * **network_id** NUMBER: Jump's network_id. SAC is 165
    * **address** TEXT: The street address where Jump thinks the bike is. Not too usable.
    * **lng** NUMBER: Longitude of the bike as first reported.
        * Due to inaccuracy of the GPS position, we round the values to 3 decimal places when 
        * comparing subsequent sightings of the same bike.
    * **lat** NUMBER: Latitude of the bike as first reported
    * **city** TEXT: The name of the city where the bike is located.
        * We assign this value as we define the "City" limits for our purposes.
    * **batt_level** NUMBER: The battery state of charge as a percentage.
    * **batt_distance** NUMBER: Distance that Jump thinks the bike can travel on this charge.
        * Not sure if this is miles or kilometers
    * **hub_id** NUMBER: Jump's hub id if the bike is in one or null.
    * **day_number** NUMBER: A calculated value derived from retrieved date as YYYYMMDD
    * **returned_to_service** INT: We set this to 1 if we are sighting the bike after a 2 hour absence. 
        * The assumption is that the bike was off network being serviced or recharged
    * **sighted** DATETIME: The datatime we first see the bike at this location.
    * **bonuses** TEXT: JSON text of any bonuses that Jump has offered on this bike at the time of sighting
    
 
* **Trip** Table
    * **id** INT
    * **jump_bike_id** NUMBER: Jump Bike's internal id
    * **origin_sighting_id** INTEGER: The id of the sighting where this bike was seen before it moved to a new location
    * **destination_sighting_id** INTEGER: The id of the sighting where the bike re-appeared on the net.
    * **miles** NUMBER: Calculated straight line distance traveled during trip.
    
