import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
GET /drinks
    it should be a public endpoint
    it should contain only the drink.short() data representation
returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''
@app.route("/drinks")
def get_drinks():
    try:
        drinks = Drink.query.all()
        if drinks is None:
            abort(400)
        formatted_drinks = [drink.short() for drink in drinks]
        
        return jsonify({
            "success": True,
            "drinks": formatted_drinks
        })
    except Exception as e:
            if isinstance(e, HTTPException):
                abort(e.code)
            abort(404)
        


'''
GET /drinks-detail
    it should require the 'get:drinks-detail' permission
    it should contain the drink.long() data representation
returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''
@app.route("/drinks-detail")
@requires_auth("get:drinks-detail")
def get_drinks_detail():
    try:
        drinks = Drink.query.all()
        formatted_drinks = [drink.long() for drink in drinks]
        
        return jsonify({
            "success": True,
            "drinks": formatted_drinks
        })
    except Exception as e:
            if isinstance(e, HTTPException):
                abort(e.code)
            abort(404)

'''
POST /drinks
    it should create a new row in the drinks table
    it should require the 'post:drinks' permission
    it should contain the drink.long() data representation
returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
    or appropriate status code indicating reason for failure
'''
@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def add_new_drink():
    body = request.get_json()    
    try:
        drink = Drink(title=body['title'], recipe=json.dumps(body['recipe']))
        if drink is None:
            abort(400)
            
        drink.insert()
        
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })
    except Exception as e:
        if isinstance(e, HTTPException):
            abort(e.code)
        abort(422)


'''
PATCH /drinks/<id>
    where <id> is the existing model id
    it should respond with a 404 error if <id> is not found
    it should update the corresponding row for <id>
    it should require the 'patch:drinks' permission
    it should contain the drink.long() data representation
returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
    or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<int:id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drink(id):
    body = request.get_json()
    if "title" not in body and "recipe" not in body:
        abort(400)
    
    try:
        drink = Drink.query.filter_by(id=id).first()
        if drink is None:
            abort(404)
        
        if "title" in body:
            drink.title = body["title"]
        if "recipe" in body:
            drink.recipe = json.dumps(body["recipe"])
            
        drink.insert()
        
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })
    except Exception as e:
        if isinstance(e, HTTPException):
            abort(e.code)
        abort(422)

'''
DELETE /drinks/<id>
    where <id> is the existing model id
    it should respond with a 404 error if <id> is not found
    it should delete the corresponding row for <id>
    it should require the 'delete:drinks' permission
returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
    or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<int:id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(id):
    try:
        drink = Drink.query.filter_by(id=id).first()
        if drink is None:
            abort(404)
        
        drink.delete()
        
        return jsonify({
            "success": True,
            "delete": id
        })
    except Exception as e:
        if isinstance(e, HTTPException):
            abort(e.code)
        abort(422)
        


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


'''
error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def handle_exception(e):
    return jsonify({
        "success": False,
        "message": e.error["description"],
        "error": e.error["code"]
        }), e.status_code