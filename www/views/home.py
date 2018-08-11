from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from users.admin import login_required, table_access_required
from jump.models import Sighting, Trip, Bike
from jump.views import jump
from datetime import datetime
import calendar

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
    #import pdb;pdb.set_trace()
    for x in range(0,2):
        now = now.replace(month=now.month - x)
        dr = calendar.monthrange(now.year,now.month) # -> `(first day_number, number of last day)`
        start_date = now.replace(day=1)
        month_name = start_date.strftime('%B / %Y') # Month Name / Year
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
                    avg_bikes_available = '????' #rec['city_bikes'] #place holder
                    
                    city_dict = {}
                    city_dict['city'] = current_city
                    city_dict['city_bikes'] = rec['city_bikes']
                    city_dict['city_trips'] = rec['city_trips']
                    city_dict['avg_bikes_available'] = avg_bikes_available
                    ## Averages should only be divided by the last FULL day
                    day_adjust = 1
                    if days_in_month < 2:
                        day_adjust = 0
                    city_dict['trips_per_day'] = round(rec['city_trips'] / days_in_month - day_adjust, 4)
                    city_dict['trips_per_bike_per_day'] = 'N/A'
                    if rec['city_bikes'] > 0:
                        city_dict['trips_per_bike_per_day'] = round(rec['city_trips'] / rec['city_bikes'] / days_in_month - day_adjust, 4)
                    
                    monthly_data['cities'].append(city_dict)
                    
            report_data.append(monthly_data)
    
    summary_data = jump.make_data_dict()
    #import pdb;pdb.set_trace()
    print(report_data)
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
            where bike_id in 
                (
                select bike_id from sighting where
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
    return """ and sighting.city = '{city}'"""