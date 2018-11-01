import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import os
import pytest
import tempfile

import app


@pytest.fixture
def client():
    db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
    app.app.config['TESTING'] = True
    client = app.app.test_client()

    with app.app.app_context():
        print(app.app.config['DATABASE'])
        app.init_db(app.get_db(app.app.config['DATABASE'])) 
        print(app.g.db)
        
    yield client

    os.close(db_fd)
    os.unlink(app.app.config['DATABASE'])
    
    
filespec = 'instance/test_get_data.db'

db = None

with app.app.app_context():
    db = app.get_db(filespec)
    app.init_db(db)

        
def delete_test_db():
        os.remove(filespec)
        


def test_get_data(client):
        with client as c:
            from flask import session, g
            # ensure we are logged out before we start
            result = c.get('/logout/',follow_redirects=True)   
            assert result.status_code == 200
            assert b'Logged Out' in result.data 
            assert 'user' not in session
        
            result = c.post('/jump/get_data/', data={'password': 'dog', 'password': 'password'},follow_redirects=True)
            assert result.status == '200 OK'
            assert b'Login Required' in result.data
            assert 'user' not in session
            
            
            result = c.post('/jump/get_data/', data={'username': 'admin', 'password': 'password'},follow_redirects=True)
            assert result.status == '200 OK'
            assert b'Login Required' not in result.data
            assert session['user'] == 'admin'
            assert b'error' not in result.data.lower()
            assert b'Jump Data Fetch Complete' in result.data
        
            #Now should be able to work without password
            # Just clean up the user session
            result = c.get('/logout/',follow_redirects=True)   
            assert result.status_code == 200
            assert 'user' not in session
                


############################ The final 'test' ########################
######################################################################

def test_finished():
    try:
        db.close()
        delete_test_db()
        assert True
    except:
        assert True

