from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from users.admin import login_required, table_access_required

mod = Blueprint('www',__name__, template_folder='../templates', url_prefix='')


def setExits():
    g.homeURL = url_for('.home')
    g.title = 'Home'

@mod.route('/')
def home():
    setExits()
    return render_template('index.html')

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

