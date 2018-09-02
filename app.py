from flask import Flask, render_template, g, session, url_for, request, redirect
from flask_mail import Mail

from users.database import Database
from users.models import User,Role,init_db, Pref
from users.admin import Admin
from news.models import Article

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
        """Register menu items for the user dropdown"""
        g.admin = Admin(g.db)
        g.admin.register(User,url_for('user.display'),display_name='Users',minimum_rank_required=500,roles=['admin',])
        g.admin.register(Role,url_for('role.display'),display_name='Roles',minimum_rank_required=1000)
        g.admin.register(Pref,url_for('pref.display'),display_name='Prefs',minimum_rank_required=1000)

        g.admin.register(Article,url_for('news.display'),header_row=True,display_name='News',minimum_rank_required=500)
        g.admin.register(Article,url_for('news.display'),minimum_rank_required=500)
        g.admin.register(Article,url_for('news.edit'),display_name='Add Article',minimum_rank_required=500)

@app.teardown_request
def _teardown(exception):
    if 'db' in g:
        g.db.close()

        
from www.views import home,docs
app.register_blueprint(home.mod)
app.register_blueprint(docs.mod)

from users.views import user, login, role, pref
app.register_blueprint(user.mod)
app.register_blueprint(login.mod)
app.register_blueprint(role.mod)
app.register_blueprint(pref.mod)

from jump.views import jump
app.register_blueprint(jump.mod)

from mapping.views import maps
app.register_blueprint(maps.mod)

from news.views import news
app.register_blueprint(news.mod)

if __name__ == '__main__':
    with app.app_context():
        init_db(get_db())
        
        # create the jump tables
        import jump.models
        jump.models.init_tables(get_db())
        
        import news.models
        news.models.init_tables(get_db())
            
        get_db().close()
        
        
        
    
    #app.run(host='172.20.10.2', port=5000)
    app.run()
    