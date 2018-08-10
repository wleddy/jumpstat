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
    data = current_data()
    return render_template('jump_data_response.html', result=result, data=data)
    
    
def current_data(data=None):
    """Return a dictionary of Jump Bike Activity"""
    if not data or type(data) is not dict:
        data = {}
    
    data['bikes'] = get_result_count(g.db.execute('select id from bike').fetchall())
    data['sightings'] = get_result_count(g.db.execute('select id from sighting').fetchall())
    data['trips'] = get_result_count(g.db.execute('select id from trip').fetchall())
    
    return data
    
    
def get_result_count(rec):
    if not rec:
        return 0
    else:
        return len(rec)
    