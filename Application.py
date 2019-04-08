from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Database_setup import Base, Category, Items
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open(
    'client_secrets.json', 'r').read())['web']['client_id']


app = Flask(__name__)

engine = create_engine(
    'sqlite:///itemsdb.db', connect_args={'check_same_thread': False})

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Begin Authorization code

@app.route('/login/')
def LoginFunction():
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('Login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
        # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    print "done!"
    return output
    


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
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
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

        
#
# BEGIN REST SERVICES
#


@app.route('/')
def HomePage():
    return redirect(url_for('webCategories'))


@app.route('/restservice/categories', methods=['GET'])
def restGetCategories():
    categories = session.query(Category).all()
    return jsonify(Categories=[i.serialize for i in categories])


@app.route('/restservice/categories/<int:category_id>/', methods=['GET'])
def restGetCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    return jsonify(Category=category.serialize)


@app.route('/restservice/categories/<int:category_id>/items', methods=['GET'])
def restGetItemsByCategoryId(category_id):
    items = session.query(Items).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route(
    '/restservice/categories/<int:category_id>/items/<int:item_id>',
    methods=['GET'])
def restGetItemsByCategoryAndItemId(category_id, item_id):
    item = session.query(Items).filter_by(
        category_id=category_id, id=item_id).one()
    return jsonify(Items=item.serialize)

#
# END REST SERVICES
#

#
# BEGIN WEB
#


@app.route('/categories', methods=['GET'])
def webCategories():
    #if 'username' not in login_session:
        #return redirect('/login')
    #else:
    categories = session.query(Category).all()
    return render_template('Categories.html', categories=categories)


@app.route('/categories/<int:category_id>/', methods=['GET'])
def webCategoryItems(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Items).filter_by(category_id=category.id)
    return render_template('Items.html', items=items, category=category)


@app.route('/categories/<int:category_id>/items/<int:item_id>/delete')
def webDeleteItem(category_id, item_id):
    #if 'username' not in login_session:
        #return redirect('/login')
    #else:
    itemDelete = session.query(Items).filter_by(id=item_id).one()
    session.delete(itemDelete)
    session.commit()
    return redirect(url_for('webCategoryItems', category_id=category_id))


@app.route('/categories/<int:category_id>/items/new', methods=['GET'])
def webAddItem(category_id):
    #if 'username' not in login_session:
    #    return redirect('/login')
    #else:
    newItem = Items(name='', description='', category_id=category_id)
    newItem.id = 0
    return render_template('EditItem.html', item=newItem)


@app.route('/categories/<int:category_id>/items/<int:item_id>/edit',
           methods=['GET'])
def webEditItem(category_id, item_id):
    #if 'username' not in login_session:
    #return redirect('/login')
    #else:
    updateItem = session.query(Items).filter_by(id=item_id).one()
    return render_template('EditItem.html', item=updateItem)


@app.route('/categories/<int:category_id>/items/<int:item_id>',
           methods=['POST'])
def webUpdateItem(category_id, item_id):
    #if 'username' not in login_session:
    #    return redirect('/login')
    #else:
    if item_id == 0:
        newItem = Items(name=request.form['name'],
                        description=request.form['description'],
                        category_id=category_id)
        session.add(newItem)
    else:
        updateItem = session.query(Items).filter_by(id=item_id).one()
        if request.form['name']:
            updateItem.name = request.form['name']
        if request.form['description']:
            updateItem.description = request.form['description']
        session.add(updateItem)
    session.commit()
    return redirect(url_for('webCategoryItems', category_id=category_id))

#
# END WEB
#

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
