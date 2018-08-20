from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response
from www.views.home import render_markdown_for

mod = Blueprint('docs',__name__, template_folder='../templates/docs', url_prefix='/docs')


def setExits():
    g.homeURL = url_for('www.home')
    g.aboutURL = url_for('www.about')
    g.contactURL = url_for('www.contact')
    g.title = 'Documentation'

@mod.route('/', methods=['GET',])
def docs_home():
    setExits()
    g.title = "Documentation List"

    rendered_html = render_markdown_for(mod,'/doc_home.md')
    return render_template('markdown.html',rendered_html=rendered_html)

@mod.route('/data', methods=['GET',])
@mod.route('/data/', methods=['GET',])
def docs_data():
    setExits()
    g.title = "Data Dictionary"

    rendered_html = render_markdown_for(mod,'/doc_data.md')
    return render_template('markdown.html',rendered_html=rendered_html)

