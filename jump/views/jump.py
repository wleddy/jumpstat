from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from users.admin import login_required, table_access_required

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
    #flash("Jump Data Updated. - " + result)
    return render_template('jump_data_response.html', result=result)
    
