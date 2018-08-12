from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from users.admin import login_required, table_access_required
from jump.models import Bike, Sighting, Trip

mod = Blueprint('jump',__name__, template_folder='../templates', url_prefix='/jump')


def setExits():
    #g.homeURL = url_for('.home')
    g.title = 'Jump Data Response'

@mod.route('/get_data')
@mod.route('/get_data/')
def get_data():
    setExits()
    from jump.get_data import get_jump_data
    result = get_jump_data()
    data = make_data_dict()
    return render_template('jump_data_response.html', result=result, data=data)
    
    
def make_data_dict(data=None):
    """Return a dictionary of Jump Bike Activity"""
    if not data or type(data) is not dict:
        data = {}
    
    data['bikes'] = get_result_count(g.db.execute('select id from bike').fetchall())
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
    