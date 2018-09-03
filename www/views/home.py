from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from users.admin import login_required, table_access_required
from users.utils import render_markdown_for
from jump.models import Sighting, Trip, Bike
from jump.views import jump, hourly_graph
from datetime import datetime, timedelta
import calendar
from statistics import median
import mistune # for Markdown rendering
import os

mod = Blueprint('www',__name__, template_folder='../templates', url_prefix='')


def setExits():
    g.homeURL = url_for('.home')
    g.aboutURL = url_for('.about')
    g.contactURL = url_for('.contact')
    g.title = 'Home'

@mod.route('/')
def home():
    setExits()

    rendered_html = render_markdown_for(__file__,mod,'index.md')
    report_data = get_report_data()
    summary_data = jump.make_data_dict()
    hourly_data = hourlies(1)
    hourly_graph_html = hourly_graph.hourly_graph(hourly_data)
    
    
    return render_template('index.html',
        rendered_html=rendered_html, 
        data=summary_data,
        report_data=report_data, 
        hourly_data=hourly_data,
        hourly_graph_html=hourly_graph_html,
        )


@mod.route('/about', methods=['GET',])
@mod.route('/about/', methods=['GET',])
def about():
    setExits()
    g.title = "About Jumstats"
    
    rendered_html = render_markdown_for(__file__,mod,'about.md')
            
    return render_template('markdown.html',rendered_html=rendered_html)


@mod.route('/contact', methods=['POST', 'GET',])
@mod.route('/contact/', methods=['POST', 'GET',])
def contact():
    setExits()
    g.name = 'Contact Us'
    from app import app
    from users.mailer import send_message
    rendered_html = render_markdown_for(__file__,mod,'contact.md')
    show_form = True
    context = {}
    if request.form:
        if request.form['name'] and request.form['email'] and request.form['comment']:
            context['name'] = request.form['name']
            context['email'] = request.form['email']
            context['comment'] = request.form['comment']
            context['date'] = datetime.now().isoformat(sep=" ")
            print(context)
            send_message(
                None,
                subject = "Comment from {}".format(app.config['SITE_NAME']),
                html_template = "home/email/contact_email.html",
                context = context,
                reply_to = request.form['email'],
            )
        
            show_form = False
        else:
            context = request.form
            flash('You left some stuff out.')
            
    
    return render_template('contact.html',rendered_html=rendered_html, show_form=show_form, context=context)
    
    
@mod.route('/robots.txt', methods=['GET',])
def robots():
    resp = Response("""User-agent: *
Disallow: /""" )
    resp.headers['content-type'] = 'text/plain'
    return resp

    
def get_report_data():
    now = datetime.now()
    """
    Create some containers for our data
    
    """
    report_data = []
       #make a cities list plus one element for monthly totals
    totals_title = "Network Wide *" # used when displaying data
    #cities = ['Davis','Sacramento','West Sacramento',totals_title]
    
    #for this month and last month
    for x in range(0,2):
        #import pdb;pdb.set_trace()
        network_wide_bikes_available = 0
        now = datetime.now().replace(month=datetime.now().month - x)
        dr = calendar.monthrange(now.year,now.month) # -> `(first day_number, number of last day)`
        start_date = now.replace(day=1)
        month_name = start_date.strftime('%B %Y') # Month Name / Year
        end_date = now.replace(day=dr[1]) # last day of month
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # get a list of all the cities we actually saw bikes in
        sql = 'select distinct city from sighting where retrieved >= "{start_date}" and retrieved <= "{end_date}" order by city'.format(start_date=start_date_str,end_date=end_date_str)
        city_recs = g.db.execute(sql)
        cities = []
        for city in city_recs:
            cities.append(city['city'])
        
        cities.append(totals_title)
        
        # First test is there are any sightings for this month
        #import pdb;pdb.set_trace()
        rec = g.db.execute('select min(retrieved) as first, max(retrieved) as last from sighting where retrieved >= "{start_date}" and retrieved <= "{end_date}"'.format(start_date=start_date_str,end_date=end_date_str)).fetchone()
        if rec and rec['first'] != None and rec['last'] != None:
            # Get the number of days in this date range
            days_to_average_over = int(rec['last'][8:10]) - (int(rec['first'][8:10])) + 1
            if days_to_average_over < 1:
                days_to_average_over = 1 #protect against divide by zero

            monthly_data = {}
            monthly_data['month_name'] = month_name
            monthly_data['days_to_average_over'] = days_to_average_over
            monthly_data['cities'] = []
            
            # Get bikes and trips observed for all cities
            for current_city in cities:
                if current_city != totals_title:
                    city_clause = get_sql_for_city_clause().format(city=current_city)
                else:
                    city_clause = ''
                
                sql = get_sql_for_bikes_and_trips().format(city_clause=city_clause,start_date=start_date_str,end_date=end_date_str)
    
                rec = g.db.execute(sql).fetchone()
                if rec:
                    
                    # Get the median of available bikes for these sightings
                    avg_bikes_available = 0 #place holder
                    sql = get_available_bikes_sql().format(city_clause=city_clause,start_date=start_date_str,end_date=end_date_str)
                    avail = g.db.execute(sql).fetchall()

                    if not avail:
                        avg_bikes_available = 0
                    elif current_city != totals_title:
                        avg_bikes_available = int(median([x['bikes_available'] for x in avail ]))
                        network_wide_bikes_available += avg_bikes_available
                        
                    if current_city == totals_title:
                        avg_bikes_available = network_wide_bikes_available  
                    
                    
                    city_dict = {}
                    city_dict['city'] = current_city
                    city_dict['city_bikes'] = rec['city_bikes']
                    city_dict['city_trips'] = rec['city_trips']
                    city_dict['avg_bikes_available'] = avg_bikes_available
                    """ 
                        Averages should only be divided by the number of FULL days.
                    
                        If it's not the last day of the month we are currently processing
                        then we need to get the counts for just the full days of this month.
                        
                    """
                    #import pdb;pdb.set_trace()
                    day_adjust = 0
                    if start_date.day < end_date.day and days_to_average_over >= 2:
                        #get the data for just the full days of this month
                        avg_end_date_str = end_date.strftime('%Y-%m-%d')
                        sql = get_sql_for_bikes_and_trips().format(city_clause=city_clause,start_date=start_date_str,end_date=avg_end_date_str)
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
                        # This should only happen during the first day of data collection each month
                        city_dict['trips_per_day'] = 'N/A'
                        city_dict['trips_per_bike_per_day'] = 'N/A'
                        
                    if city_bikes <=0:
                        city_bikes = 1 # Protect against divide by zero
                        
                    if days_to_average_over >= 2:
                        city_dict['trips_per_day'] = '{:.2f}'.format(round(city_trips / (days_to_average_over - day_adjust), 2)) 
                        city_dict['trips_per_bike_per_day'] = '{:.2f}'.format(round((city_trips /  (days_to_average_over - day_adjust) / city_bikes), 2))
                    
                    monthly_data['cities'].append(city_dict)
                    
            report_data.append(monthly_data)
    
    return report_data
    
def get_sql_for_bikes_and_trips():
    return """-- Get the total bikes and total trip for each city
        select 
            -- Bikes observed in city in date range
            (
            select count() from bike
            where jump_bike_id in 
                (
                select jump_bike_id from sighting where
                sighting.retrieved >= '{start_date} 00:00:00' and sighting.retrieved <= '{end_date} 23:59:59' {city_clause}
                )
            ) as city_bikes, 
            -- Trips observed in city in date range
            (
            select count() from trip
            where trip.destination_sighting_id in 
                (
                select id from sighting where
                sighting.retrieved >= '{start_date} 00:00:00' and sighting.retrieved <= '{end_date} 23:59:59' {city_clause}
                )
            ) as city_trips
        from bike limit 1;
    """
    
def get_sql_for_city_clause():
    return """ and city = '{city}'"""
    
def get_available_bikes_sql():
    return """select bikes_available from available_bike_count
where retrieved >= '{start_date}' and retrieved <= '{end_date}' {city_clause}
"""

def hourlies(days_to_report=1):
    """
    Return a dictionary designed to be used to report on
    the hourly bike usage and availability
    
    Returns 12 hours of data stating 24 hours before now in a dictionary like so:
    
    {'start_date': 'a date string','end_date: 'a date string, 'days': nnumber of days in report,
        'hours': [ hours 0-23 in the order to report], 
        'trips':[ int values of trips for each our ], 'bikes': [ int values of bike counts for each hour],
        'max_bikes': highest in 'bikes', 'max_trips': highest in 'trips', 
    }
    If no data is found at all, retruns None
    """
    if days_to_report <= 0:
        days_to_report = 1
        
    hourly_data = {}
    hourly_data['hours'] = []
    end_date = datetime.now().replace(minute=0,second=0,microsecond=0) - timedelta(minutes=1)
    start_date = end_date - timedelta(days=days_to_report) + timedelta(minutes=1)
    hourly_data['start_date'] = start_date.strftime('%B %-d, %Y %-I:%M %p')
    hourly_data['end_date'] = end_date.strftime('%B %-d, %Y %-I:%M %p')
    trip_list = []
    bike_list = []
    max_bikes = 0
    max_trips = 0
    has_data = False
    for hour in range(24):
        query_start = start_date
        query_end = query_start + timedelta(minutes=59)
        
        hourly_data['hours'].append(start_date.hour)
        sql = """select count(trip.id) as trip_count from trip 
            join sighting on destination_sighting_id = sighting.id
            where sighting.retrieved >= '{}' and sighting.retrieved <= '{}'
            """.format(query_start.isoformat(sep=" "),query_end.isoformat(sep=" "))
        trip_cnt = g.db.execute(sql).fetchone()
        sql = """select avg(bikes_available) as bikes from available_bike_count 
            where retrieved >= '{}' and retrieved <= '{}' group by city 
            """.format(query_start.isoformat(sep=" "),query_end.isoformat(sep=" "))
        bike_cnt = g.db.execute(sql).fetchall()
        if trip_cnt and bike_cnt:
            has_data = True
            cnt = int(trip_cnt['trip_count']/days_to_report)
            trip_list.append(cnt)
            if cnt > max_trips:
                max_trips = cnt
            
            cnt = 0
            for x in bike_cnt:
                cnt += x['bikes']
            
            cnt = int(cnt)
            bike_list.append(cnt)
            if cnt > max_bikes:
                max_bikes = cnt
        else:
            trip_list.append(0)
            bike_list.append(0)
 
        start_date = start_date + timedelta(hours=1)
        
    if has_data:
        hourly_data['trips'] = trip_list
        hourly_data['bikes'] = bike_list
        hourly_data['max_bikes'] = max_bikes
        hourly_data['max_trips'] = max_trips
        hourly_data['days'] = days_to_report
        return hourly_data
    else:
        return None

    
