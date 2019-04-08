from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Database_setup import Base, Category, Items
from flask import session as login_session
import random, string 

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']


app = Flask(__name__)

engine = create_engine('sqlite:///itemsdb.db', connect_args={'check_same_thread': False})

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#
#Begin Authorization code
#
@app.route('/login/')
def LoginFunction():
     state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
     login_session['state'] = state
     return render_template('ServerTest.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        # Put Auth code into object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        print "About to get 401 error"

        return response

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
        #return redirect(url_for('LoginFunction'))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

#
# BEGIN REST SERVICES
#

@app.route('/restservice/categories', methods = ['GET'])
def restGetCategories():
    categories = session.query(Category).all()
    return jsonify(Categories=[i.serialize for i in categories])


@app.route('/restservice/categories/<int:category_id>/', methods = ['GET'])
def restGetCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    return jsonify(Category=category.serialize)

@app.route('/restservice/categories/<int:category_id>/items', methods = ['GET'])
def restGetItemsByCategoryId(category_id):
    items = session.query(Items).filter_by(category_id = category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/restservice/categories/<int:category_id>/items/<int:item_id>', methods = ['GET'])
def restGetItemsByCategoryAndItemId(category_id,item_id):
    item = session.query(Items).filter_by(category_id = category_id, id = item_id).one()
    return jsonify(Items=item.serialize)

#
# END REST SERVICES
#



#
# BEGIN WEB
#

@app.route('/categories', methods=['GET'])
def webCategories():
    if 'username' not in login_session:
        return redirect('/login')
    else:
        categories = session.query(Category).all()
        return render_template('Categories.html',categories=categories)


@app.route('/categories/<int:category_id>/', methods=['GET'])
def webCategoryItems(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Items).filter_by(category_id = category.id)
    return render_template('Items.html', items = items, category=category)


@app.route('/categories/<int:category_id>/items/<int:item_id>/delete')
def webDeleteItem(category_id,item_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        itemDelete = session.query(Items).filter_by(id = item_id).one()
        session.delete(itemDelete)
        session.commit()
        return redirect(url_for('webCategoryItems', category_id = category_id))
    
@app.route('/categories/<int:category_id>/items/new',methods=['GET'])
def webAddItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        newItem = Items(name = '', description = '', category_id = category_id)
        newItem.id = 0
        return render_template('EditItem.html', item = newItem )

@app.route('/categories/<int:category_id>/items/<int:item_id>/edit', methods=['GET'])
def webEditItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        updateItem = session.query(Items).filter_by(id = item_id).one()
        return render_template('EditItem.html', item = updateItem)
    
@app.route('/categories/<int:category_id>/items/<int:item_id>', methods=['POST'])
def webUpdateItem(category_id,item_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        if item_id == 0:
            newItem = Items(name = request.form['name'], description = request.form['description'], category_id = category_id)
            session.add(newItem)
        else:
            updateItem = session.query(Items).filter_by(id = item_id).one()
            if request.form['name']:
                updateItem.name = request.form['name']
            if request.form['description']:
                updateItem.description = request.form['description']
            session.add(updateItem)
    session.commit()
    return redirect(url_for('webCategoryItems', category_id = category_id))




#
# END WEB
#

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True 
    app.run(host='0.0.0.0', port=5000)