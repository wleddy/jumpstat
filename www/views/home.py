from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from users.admin import login_required, table_access_required
from jump.models import Sighting, Trip, Bike
from jump.views import jump
from datetime import datetime
import calendar
from statistics import median

mod = Blueprint('www',__name__, template_folder='../templates', url_prefix='')


def setExits():
    g.homeURL = url_for('.home')
    g.title = 'Home'

@mod.route('/')
def home():
    setExits()

    now = datetime.now()
    """
    Create some containers for our data
    
    """
    report_data = []
       #make a cities list plus one element for monthly totals
    totals_title = "Network Wide *" # used when displaying data
    cities = ['Davis','Sacramento','West Sacramento',totals_title]
    
    #for this month and last month
    for x in range(0,2):
        now = datetime.now().replace(month=datetime.now().month - x)
        dr = calendar.monthrange(now.year,now.month) # -> `(first day_number, number of last day)`
        start_date = now.replace(day=1)
        month_name = start_date.strftime('%B %Y') # Month Name / Year
        end_date = now.replace(day=dr[1]) # last day of month
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # First test is there are any sightings for this month
        rec = g.db.execute('select min(retrieved) as first, max(retrieved) as last from sighting where retrieved >= "{start_date}" and retrieved <= "{end_date}"'.format(start_date=start_date_str,end_date=end_date_str)).fetchone()
        
        #import pdb;pdb.set_trace()
        
        if rec and rec['first'] != None and rec['last'] != None:
            # Get the number of days in this date range
            days_in_month = int(rec['last'][8:10]) - (int(rec['first'][8:10])) + 1
            if days_in_month < 1:
                days_in_month = 1 #protect against divide by zero

            monthly_data = {}
            monthly_data['month_name'] = month_name
            monthly_data['days_in_month'] = days_in_month
            monthly_data['cities'] = []
            # Get bikes and trips observed for all cities
            for current_city in cities:
                if current_city != totals_title:
                    city_clause = get_city_clause_sql().format(city=current_city)
                else:
                    city_clause = ''
                
                sql = get_date_select_sql().format(city_clause=city_clause,start_date=start_date_str,end_date=end_date_str)
    
                rec = g.db.execute(sql).fetchone()
                if rec:
                    
                    # Get the median of available bikes for these sightings
                    avg_bikes_available = '- N/A -' #place holder
                    sql = get_available_bikes_sql().format(city_clause=city_clause,start_date=start_date_str,end_date=end_date_str)
                    avail = g.db.execute(sql).fetchall()
                    #import pdb;pdb.set_trace()
                    if avail and current_city != totals_title:
                        avg_bikes_available = int(median([x['bikes_available'] for x in avail ]))
                    
                    
                    city_dict = {}
                    city_dict['city'] = current_city
                    city_dict['city_bikes'] = rec['city_bikes']
                    city_dict['city_trips'] = rec['city_trips']
                    city_dict['avg_bikes_available'] = avg_bikes_available
                    ## Averages should only be divided by the last FULL day
                    day_adjust = 0
                    if datetime.now().day < end_date.day and days_in_month > 2:
                        #get the data for just the full days of this month
                        avg_date = datetime.now().replace(day=datetime.now().day -1)
                        avg_end_date_str = avg_date.strftime('%Y-%m-%d')
                        sql = get_date_select_sql().format(city_clause=city_clause,start_date=start_date_str,end_date=avg_end_date_str)
                        avg_rec = g.db.execute(sql).fetchone()
                        if avg_rec:
                            city_trips = avg_rec['city_trips']
                            city_bikes = avg_rec['city_bikes']
                            day_adjust = 1
                        else:
                            city_trips = rec['city_trips']
                            city_bikes = rec['city_bikes']
                            day_adjust = 0
                    else:
                        # to avoid divide by zero error
                        # This should only happen during the first day of data collection
                        city_trips = 1
                        city_bikes = 1
                        
                        city_dict['trips_per_day'] = '{:.2f}'.format(round(city_trips / (days_in_month - day_adjust), 2)) 
                    city_dict['trips_per_bike_per_day'] = 'N/A'
                    if city_bikes > 0:
                        city_dict['trips_per_bike_per_day'] = '{:.2f}'.format(round((city_trips /  (days_in_month - day_adjust) / city_bikes), 2))
                    
                    monthly_data['cities'].append(city_dict)
                    
            report_data.append(monthly_data)
    
    summary_data = jump.make_data_dict()
    #import pdb;pdb.set_trace()

    return render_template('index.html',data=summary_data,report_data=report_data)

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
    
@mod.route('/robots.txt')
def robots():
    resp = Response("""User-agent: *
Disallow: /""" )
    resp.headers['content-type'] = 'text/plain'
    return resp


def get_date_select_sql():
    return """-- Get the total bikes and total trip for each city
        select 
            -- Bikes observed in city in date range
            (
            select count() from bike
            where jump_bike_id in 
                (
                select jump_bike_id from sighting where
                sighting.retrieved >= '{start_date}' and sighting.retrieved <= '{end_date}' {city_clause}
                )
            ) as city_bikes, 
            -- Trips observed in city in date range
            (
            select count() from trip
            where trip.destination_sighting_id in 
                (
                select id from sighting where
                sighting.retrieved >= '{start_date}' and sighting.retrieved <= '{end_date}' {city_clause}
                )
            ) as city_trips
        from bike limit 1;
    """
    
def get_city_clause_sql():
    return """ and city = '{city}'"""
    
def get_available_bikes_sql():
    return """select bikes_available from available_bike_count
where retrieved >= '{start_date}' and retrieved <= '{end_date}' {city_clause}
"""
