import os
from flask import Flask, request, jsonify, abort
from pkg_resources import require
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES


@app.route('/drinks')
def get_drinks():
    soft_drinks = Drink.query.all()
    drinks = [drink.short() for drink in soft_drinks]
    return jsonify(
        {
            'success': True,
            'drinks': drinks
        }
    )


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def drinks_detail(jwt):
    soft_drinks = Drink.query.all()
    drinks = [drink.long() for drink in soft_drinks]
    return jsonify(
        {
            'success': True,
            'drinks': drinks
        }
    )


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    data = request.get_json()

    title = data.get('title', None)
    recipe = data.get('recipe', None)
    recipe_details = str(recipe)
    recipe_details = recipe_details.replace("\'", "\"")
    soft_drink = Drink(title=title, recipe=recipe_details)

    soft_drink.insert()
    drink = soft_drink.long()

    return jsonify(
        {
            'success': True,
            'drinks': drink
        }
    )


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, drink_id):
    data = request.get_json()

    try:
        title = data.get('title', None)
        soft_drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

        if title is not None:
            soft_drink.title = title
        try:
            soft_drink.update()

            drink = [soft_drink.long()]
            return jsonify(
                {
                    'success': True,
                    'drinks': drink
                }
            )
        except Exception as e:
            abort(400)
    except BaseException:
        abort(404)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    drink.delete()
    return jsonify(
        {
            'success': True,
            'delete': drink_id
        }
    )


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


@app.errorhandler(404)
def resourcenotfound(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(AuthError)
def notauthenticated(error):
    return jsonify({
        "success": False,
        "error": error.code,
        "message": "Authentication Error"
    }), error.code
