import os
from unicodedata import category
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        database_user = os.getenv('DB_USER')
        database_password = os.getenv('DB_PASSWORD')
        self.database_path = 'postgresql://{}:{}@{}/{}'.format(database_user, database_password, 'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        self.new_question = {
            "question": "What is the capital city of Nigeria ?",
            "answer": "Abuja", 
            "category": 3, 
            "difficulty": 1
        }

        self.incomplete_question = {
            "category": 1, 
            "difficulty": 1
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_categories(self):
        res = self.client().get("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["categories"])

    def test_get_paginated_questions(self):
        res = self.client().get("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(len(data["questions"]))

    def test_404_sent_requesting_questions_beyond_valid_page(self):
        res = self.client().get("/questions?page=100")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Resource Not Found")
    
    def test_create_new_question(self):
        res = self.client().post("/questions", json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
    
    def test_create_new_question_without_required_property(self):
        res = self.client().post("/questions", json=self.incomplete_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Bad Request")
    
    def test_search_question_found(self):
        res = self.client().post("/questions", json={'searchTerm': ' '})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertNotEqual(len(data["questions"]), 0)
        self.assertNotEqual(data["totalQuestions"], 0)
        self.assertNotEqual(data["currentCategory"], '')
    
    def test_search_question_not_found(self):
        res = self.client().post("/questions", json={'searchTerm': 'nigeria'})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], False)
        self.assertEqual(len(data["questions"]), 0)
        self.assertEqual(data["totalQuestions"], 0)
        self.assertEqual(data["currentCategory"], '')
    
    def test_delete_question(self):
        question = Question.query.filter(Question.question.ilike('%nigeria%')).first()
        res = self.client().delete("/questions/{}".format(question.id))
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["deleted"], question.id)
    
    def test_delete_question_which_is_not_exist(self):
        question_id = 1000
        res = self.client().delete("/questions/{}".format(question_id))
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "unprocessable")
    
    def test_get_question_of_category(self):
        category_id = 1
        res = self.client().get("/categories/{}/questions".format(category_id))
        data = json.loads(res.data)
        category = Category.query.get(category_id)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertNotEqual(len(data["questions"]), 0)
        self.assertNotEqual(data["totalQuestions"], 0)
        self.assertEqual(data["currentCategory"], category.type)
    
    def test_quizzes(self):
        body = {
            'previous_questions': [], 
            'quiz_category': {
                'id': 0,
                'type': ''
            }
        }
        res = self.client().post("/quizzes", json=body)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertNotEqual(data["question"]["id"], 0)
    
    def test_quizzes_return_code_500_with_query_with_empty_body(self):
        body = {}
        res = self.client().post("/quizzes", json=body)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], 'Bad Request')


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()