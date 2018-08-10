from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from users.admin import login_required, table_access_required
from jump.models import Sighting, Trip, Bike
from jump.views.jump import current_data
from datetime import datetime
import calendar

mod = Blueprint('www',__name__, template_folder='../templates', url_prefix='')


def setExits():
    g.homeURL = url_for('.home')
    g.title = 'Home'

@mod.route('/')
def home():
    setExits()
    data = {}
    # get the current month
    now = datetime.now()
    dr = calendar.monthrange(now.year,now.month) # -> `(first day_number, number of last day)`
    start_date = now.replace(day=1)
    end_date = now.replace(day=dr[1]) # last day of month
    
    sql = """
    -- Count bikes by city -- Quotes around date string is important, i think...
    select count(bike.bike_id) as bike_count, sighting.city as city from sighting
    inner join bike on sighting.bike_id = bike.bike_id
    where sighting.retrieved >= '{}' and sighting.retrieved <= '{}'
    group by sighting.city
    order by sighting.city
    """.format(start_date.strftime('%Y-%m-%d'),end_date.strftime('%Y-%m-%d'))
    bikes = g.db.execute(sql).fetchall()
    bike_counts = []
    for bike in bikes:
        keys = bike.keys()
        #print(bike)
        #import pdb;pdb.set_trace()
        data = {}
        for key in keys:
            #print('{}: {}'.format(key,bike[key]))
            data[key] =bike[key]
        bike_counts.append(data)
    
    #print (bike_counts)
    
    # Get the trip counts
    sql = """
    -- Count trips by City
    select count(sighting.bike_id), sighting.city from sighting
    inner join trip on sighting.id = trip.destination_sighting_id
    where sighting.retrieved >= '{}' and sighting.retrieved <= '{}'
    group by sighting.city
    order by sighting.city""".format(start_date.strftime('%Y-%m-%d'),end_date.strftime('%Y-%m-%d'))
    
    data = current_data(data)
    
    return render_template('index.html',data=data)

@mod.route('/about')
@mod.route('/about/')
def about():
    setExits()
    g.name = "About Us"
    return "About us text goes here"

@mod.route('/contact')
@mod.route('/contact/')
def contact():
    setExits()
    g.name = 'Contact Us'
    return "contact form goes here"

