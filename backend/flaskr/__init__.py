from crypt import methods
import os
import re
from unicodedata import category
from urllib import response
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, questions):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        formatted_questions = [question.format() for question in questions]
        current_questions = formatted_questions[start:end]
        return current_questions

"""
Get the Categories as a Dictionniare data type
"""
def get_categories_as_dict():
    categories = Category.query.all()
    dict = {}
    for category in categories:
        dict[category.id] = category.type
    return dict

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"*" : {"origins": '*'}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = get_categories_as_dict()

        return jsonify({
            'success': True,
            'categories': categories
            })


    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions', methods=['GET'])
    def get_questions():
        questions = Question.query.all()
        current_questions = paginate_questions(request, questions)
        if len(current_questions) == 0:
            abort(404)

        current_question = current_questions[0]
        current_category = current_question['category']
        categories = get_categories_as_dict()

        return jsonify({
            'success': True,
            'questions': current_questions,
            'totalQuestions': len(questions),
            'categories': categories,
            'currentCategory': categories[current_category]
        })

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)
            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })

        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def create_questions():
        body = request.get_json()
        if 'searchTerm' in body:
            # Request to search a question
            search_term = "%{}%".format(body.get('searchTerm'))
            questions = Question.query.filter(Question.question.ilike(search_term)).all()
            if len(questions) == 0:
                #abort(404)
                return jsonify({
                    'success': False,
                    'questions': [],
                    'totalQuestions': 0,
                    'currentCategory': ''
                })

            formatted_questions = [question.format() for question in questions]
            current_category = Category.query.get(formatted_questions[0]['category'])

            return jsonify({
                'success': True,
                'questions': formatted_questions,
                'totalQuestions': len(questions),
                'currentCategory': current_category.type
            })

        else:
            # Request to create a new question
            the_question = body.get('question', None)
            the_answer = body.get('answer', None)
            the_category = body.get('category')
            the_difficulty = body.get('difficulty')

            try:
                new_question = Question(question=the_question, answer=the_answer, category=the_category, difficulty=the_difficulty)
                new_question.insert()

                return jsonify({
                    'success': True
                })
            
            except:
                abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_from_category(category_id):
        questions = Question.query.filter(Question.category==category_id).all()
        if len(questions) == 0:
                #abort(404)
                return jsonify({
                    'success': False,
                    'questions': [],
                    'totalQuestions': 0,
                    'currentCategory': ''
                })

        formatted_questions = [question.format() for question in questions]
        current_category = Category.query.get(category_id)

        return jsonify({
                'success': True,
                'questions': formatted_questions,
                'totalQuestions': len(questions),
                'currentCategory': current_category.type
            })

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def play_quizz():
        body = request.get_json()
        previous_question_id = body.get('previous_questions')
        quiz_category = body.get('quiz_category')
        next_question = Question(question='', answer='', category=0, difficulty=0)
        if quiz_category['id'] == 0:
            next_question = Question.query.filter(~Question.id.in_(previous_question_id)).first()
        else:
            next_question = Question.query.filter(~Question.id.in_(previous_question_id)).filter(Question.category==quiz_category['id']).first()

        if next_question is None:
            abort(404)

        return jsonify({
            'success': True,
            'question': next_question.format()
        })

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Resource Not Found'
        }), 404
    
    @app.errorhandler(422)
    def unprocessable_error(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }), 422
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'Server Error'
        }), 500

    return app

