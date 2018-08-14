from flask import Flask, render_template, g, session, url_for, request, redirect
from flask_mail import Mail

from users.database import Database
from users.models import User,Role,init_db
from users.admin import Admin

# Create app
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('site_settings.py', silent=True)


# work around some web servers that mess up root path
from werkzeug.contrib.fixers import CGIRootFix
if app.config['CGI_ROOT_FIX_APPLY'] == True:
    fixPath = app.config.get("CGI_ROOT_FIX_PATH","/")
    app.wsgi_app = CGIRootFix(app.wsgi_app, app_root=fixPath)


# Create a mailer obj
mail = Mail(app)


def get_db(filespec=app.config['DATABASE_PATH']):
    if 'db' not in g:
        g.db = Database(filespec).connect()
    return g.db


@app.before_request
def _before():
    # Force all connections to be secure
    if app.config['REQUIRE_SSL'] and not request.is_secure :
        return redirect(request.url.replace("http://", "https://"))
        
    get_db()
    
    # Is the user signed in?
    g.user = None
    if 'user' in session:
        g.user = session['user']
        
    if 'admin' not in g:
        g.admin = Admin(g.db)
        g.admin.register(User,url_for('user.display'),display_name='Users',minimum_rank_required=500,roles=['admin',])
        g.admin.register(Role,url_for('role.display'),display_name='Roles',minimum_rank_required=1000)


@app.teardown_request
def _teardown(exception):
    if 'db' in g:
        g.db.close()

#from jump.get_jump_bikes import InfiniteTimer,get_jump_data
#
#t = InfiniteTimer(10.0, get_jump_data)
#t.start()
#t.start()

#from jump.get_jump_bikes import begin_timer
#begin_timer(app.config['JUMP_REQUEST_SECONDS'])
#begin_timer(10.0)
        
from www.views import home
app.register_blueprint(home.mod)

from users.views import user, login, role
app.register_blueprint(user.mod)
app.register_blueprint(login.mod)
app.register_blueprint(role.mod)

from jump.views import jump
app.register_blueprint(jump.mod)

if __name__ == '__main__':
    with app.app_context():
        init_db(get_db())
        
        # create the jump tables
        from jump.models import init_tables
        init_tables(get_db())
        
        get_db().close()
        
        
        
    
    #app.run(host='172.20.10.2', port=5000)
    app.run()
    