## Map view of trips
from flask import g, redirect, url_for, \
     render_template, flash, Blueprint, request
from users.utils import printException
import json
from datetime import datetime, timedelta

mod = Blueprint('maps', __name__,template_folder='../templates', url_prefix='/map')

def setExits():
    g.title = 'Jump Map'
    
@mod.route('/time_lapse', methods=['GET'])
def time_lapse_map(start_date='2018-08-17',days=1):
    """
    Display an automated map of bike sightings over time
    """
    
    """
    TODO - Need to "preload" the map with all the bikes that are there at the start
    of the period. They would all have a start time code of 0 and an end time code of the
    time of their last retrieval
    """
    setExits()
    days = 3
    start_date = datetime(2018,8,17) #'2018-08-17 00:00:00.0'
    end_date = start_date + timedelta(days=days,seconds=-1) 
    
    frame_duration = 10 * 60 # this many seconds of real time elapse between each frame
    seconds_per_frame = 2 # display each frame for this many seconds
    
    sql = """select id, lng, lat, sighted, retrieved from sighting where 
            sighted >= '{start_date}' and retrieved <= '{end_date}' 
            order by sighted;
        """.format(start_date=start_date.isoformat(sep=' '), end_date=end_date.isoformat(sep=' '))
        
    recs = g.db.execute(sql).fetchall()

    markerData = {"markers":[]}
    markerData["zoomToFit"] = False # can/t zoom if there are no markers.
    
    if recs:
        """
        The Marker is a list of lists containing:
            sighting id as str,
            lng,
            lat,
            display starting seconds,
            display ending seconds
        
        At play time in javascript, every frame_duration seconds loop through Markers:
            if start seconds >= time code and end seconds <= time code,
                add to map if not there
            else
                remove from map if there
        """
        # set start and end to the records retrieved
        fmt = '%Y-%m-%d %H:%M:%S.%f'
        start_date = datetime.strptime(recs[0]['sighted'],fmt)
        end_date = datetime.strptime(recs[len(recs)-1]['retrieved'],fmt)
        #print('end_date: {}'.format(end_date))
        total_seconds = int(round((end_date - start_date).total_seconds(),0))
        markerData["zoomToFit"] = True
        frame_end = frame_duration
        markerData['total_seconds'] = total_seconds
        markerData['frame_duration'] = frame_duration
        markerData['seconds_per_frame'] = seconds_per_frame
        for rec in recs:
            sighted_dt = datetime.strptime(rec['sighted'],fmt)
            #print('sighted_dt: {}'.format(sighted_dt))
            retrieved_dt = datetime.strptime(rec['retrieved'],fmt)
            #print('retrieved_dt: {}'.format(retrieved_dt))
            markerData["markers"].append([str(rec['id']),
                                        round(rec['lng'],5),
                                        round(rec['lat'],5),
                                        int(round((sighted_dt - start_date).total_seconds(),0)),
                                        int(round((retrieved_dt - start_date).total_seconds(),0)),
                                    ])
                                
        #print(markerData)
        #print(sql)
        #print('recs = {}'.format(len(recs)))
    #return('Ok')
    return render_template('JSONmap.html', markerData=markerData)


@mod.route('/report/mapError', methods=['GET'])
@mod.route('/report/mapError/', methods=['GET'])
@mod.route('/report/mapError/<errorMessage>/', methods=['GET'])
def mapError(errorMessage=""):
    setExits()
    return render_template('mapError.html', errorMessage=errorMessage)
    
    
def escapeTemplateForJson(popup):
    # json doesn't like some characters rendered from the template
    if type(popup) != str and type(popup) != unicode:
        popup = ''
    popup = popup.replace('"','\\"') # to escape double quotes in html
    popup = popup.replace('\r',' ') # replace any carriage returns with space
    popup = popup.replace('\n',' ') # replace any new lines with space
    popup = popup.replace('\t',' ') # replace any tabs with space
    
    return popup
    

def getDivIcon(markerCount):
    """
    return an HTML block to be used as the DivIcon for a marker
    """
    if not markerCount:
        markerCount = "n/a"
    markerName = "BikeMarker_Blue.png"

    if type(markerCount) is int:
        if markerCount > 19:
            markerName = "BikeMarker_Green.png"
        if markerCount > 99:
            markerName = "BikeMarker_Gold.png"
        if markerCount > 199:
            markerName = "BikeMarker_Red.png"
            
    divIcon = render_template("map/divIcon.html", markerName=markerName, markerCount=markerCount)
    
    return escapeTemplateForJson(divIcon)
    

    
    