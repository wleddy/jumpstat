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
@mod.route('/time_lapse/', methods=['GET'])
def time_lapse_map():
    """
    Display an automated map of bike sightings over time
    """
    setExits()
    days = 1
    start_date = datetime.now() + timedelta(days=-1) # Always starts at midnight, yesterday
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=days,seconds=-1) 
    
    frame_duration = 10 * 60 # this many seconds of real time elapse between each frame
    seconds_per_frame = 1 # display each frame for this many seconds
        
    sql = """select id, lng, lat, sighted, retrieved from sighting where 
            retrieved >= '{start_date}' and sighted <= '{end_date}' 
            order by sighted
        """.format(start_date=start_date.isoformat(sep=' '), end_date=end_date.isoformat(sep=' '))
        
    recs = g.db.execute(sql).fetchall()

    markerData = {"markers":[]}
    markerData["zoomToFit"] = False # can/t zoom if there are no markers.
    
    if recs:
        """
        The Marker is a list of lists containing:
            lng,
            lat,
            display start seconds,
            display end seconds
        
        At play time in javascript, every frame_duration seconds loop through Markers:
            if display start seconds <= frame start time and display end seconds >= frame end time,
                set the marker opacity to 1
            else
                set opacity to 0
        """
        
        fmt = '%Y-%m-%d %H:%M:%S.%f'
        total_seconds = int(round((end_date - start_date).total_seconds(),0))
        markerData["zoomToFit"] = True
        markerData['total_seconds'] = total_seconds
        markerData['frame_duration'] = frame_duration
        markerData['seconds_per_frame'] = seconds_per_frame
        
        #import pdb;pdb.set_trace()
        for rec in recs:
            sighted_dt = datetime.strptime(rec['sighted'],fmt)
            if sighted_dt.day == 17:
                #import pdb;pdb.set_trace()
                pass
            #print('sighted_dt: {}'.format(sighted_dt))
            retrieved_dt = datetime.strptime(rec['retrieved'],fmt)
            #print('retrieved_dt: {}'.format(retrieved_dt))
            markerData["markers"].append([round(rec['lng'],5),
                                        round(rec['lat'],5),
                                        int(round((sighted_dt - start_date).total_seconds(),0)),
                                        int(round((retrieved_dt - start_date).total_seconds(),0)),
                                    ])
                                
        #print(markerData)
        #print(sql)
        #print('recs = {}'.format(len(recs)))
    #return('Ok')
    return render_template('JSONmap.html', markerData=markerData,start_date=start_date)


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
    

    
    