from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from users.admin import login_required, table_access_required, silent_login
from jump.models import Bike, Sighting, Trip
from datetime import timedelta
from date_utils import local_datetime_now

mod = Blueprint('jump',__name__, template_folder='../templates', url_prefix='/jump')


def setExits():
    #g.homeURL = url_for('.home')
    g.title = 'Jump Data Response'

@mod.route('/get_data', methods=['GET','POST'])
@mod.route('/get_data/', methods=['GET','POST'])
@silent_login()
def get_data():
    setExits()
    #from jump.get_data import get_jump_data
    #result = get_jump_data()
    from jump.get_GBFS_data import get_gbfs_data
    result = get_gbfs_data()
    data = make_data_dict()
    return render_template('jump_data_response.html', result=result, data=data)
    
    
def make_data_dict(data=None):
    """Return a dictionary of Jump Bike Activity"""
    if not data or type(data) is not dict:
        data = {}
    
    # limit bike count to last 2 days
    local_time = local_datetime_now()
    start_date = (local_time - timedelta(days=2)).isoformat(sep=' ')
    end_date = local_time.isoformat(sep=' ')
    data['bikes'] = get_result_count(g.db.execute('select distinct jump_bike_id from sighting where retrieved >= "{}" and retrieved <= "{}"'.format(start_date,end_date,)).fetchall())
    data['sightings'] = get_result_count(g.db.execute('select id from sighting').fetchall())
    data['trips'] = get_result_count(g.db.execute('select id from trip').fetchall())
    data['available'] = 0
    data['retrieval_date'] = 'Unknown'
    
    sql = """select count(jump_bike_id) as avail, retrieved from sighting
                group by retrieved
                order by retrieved desc
                limit 1
            """
    rec = g.db.execute(sql).fetchall()
    if rec and len(rec) > 0:
        data['available'] = rec[0]['avail']
        data['retrieval_date'] = str(rec[0]['retrieved'])[:16]
    return data
    
    
def get_result_count(rec):
    if not rec:
        return 0
    else:
        return len(rec)
    