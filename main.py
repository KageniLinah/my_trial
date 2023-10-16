from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Asylum_105@localhost/Trial_Database'
db = SQLAlchemy(app)


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255))
    answer = db.Column(db.String(255))
    time_limit = db.Column(db.Integer)


class QuizTaker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    score = db.Column(db.Integer)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)


@app.before_first_request
def init_db():
    db.create_all()
    quiz1 = Quiz(question='Q 1/3 What is the capital of France?', answer='Paris', time_limit=10)
    quiz2 = Quiz(question='Q 2/3 What is the largest planet in our solar system?', answer='Jupiter', time_limit=20)
    quiz3 = Quiz(question='Q 3/3 Who wrote the Harry Potter series?', answer='J.K. Rowling', time_limit=30)
    db.session.add_all([quiz1, quiz2, quiz3])
    db.session.commit()


@app.route('/', methods=['POST', 'GET'])
def ussd():
    session_id = request.values.get('sessionId', None)
    service_code = request.values.get('serviceCode', None)
    phone_number = request.values.get('phoneNumber', None)
    text = request.values.get('text', 'default')

    text_list = text.split('*')
    user_response = text_list[-1]

    if text == '':
        response = 'CON Welcome to the Quiz. Choose an option:\n1. Register\n2. Login\n3. Quit'
    elif text == '1':
        response = 'CON Enter your username:'
    elif len(text_list) == 2 and text_list[0] == '1':
        username = user_response
        quiz_taker = QuizTaker(username=username)
        db.session.add(quiz_taker)
        db.session.commit()
        response = 'END You have been registered successfully.'
    elif text == '2':
        response = 'CON Enter your username:'
    elif len(text_list) == 2 and text_list[0] == '2':
        username = user_response
        quiz_taker = QuizTaker.query.filter_by(username=username).first()
        if quiz_taker:
            quiz = Quiz.query.first()
            quiz_taker.quiz_id = quiz.id
            quiz_taker.start_time = datetime.now()
            quiz_taker.end_time = quiz_taker.start_time + timedelta(seconds=quiz.time_limit)
            db.session.commit()
            response = f'CON {quiz.question}'
        else:
            response = 'END Invalid username.'
    elif len(text_list) == 3 and text_list[0] == '2':
        answer = user_response
        username = text_list[1]
        quiz_taker = QuizTaker.query.filter_by(username=username).first()
        quiz = Quiz.query.filter_by(id=quiz_taker.quiz_id).first()
        if datetime.now() > quiz_taker.end_time:
            quiz_taker.score = 0
            db.session.commit()
            response = 'END Time is up!'
        else:
            if answer.lower() == quiz.answer.lower():
                quiz_taker.score = 1
            else:
                quiz_taker.score = 0
            db.session.commit()
            next_quiz = Quiz.query.filter(Quiz.id > quiz.id).first()
            if next_quiz:
                quiz_taker.quiz_id = next_quiz.id
                quiz_taker.start_time = datetime.now()
                quiz_taker.end_time = quiz_taker.start_time + timedelta(seconds=next_quiz.time_limit)
                db.session.commit()
                response = f'CON Next question: {next_quiz.question}'
            else:
                response = f'END You have completed the quiz. Your score is {quiz_taker.score}.'

    else:
        response = 'END Invalid input.'

    return response


if __name__ == '__main__':
    app.run(port=80, host="localhost", debug=True)

