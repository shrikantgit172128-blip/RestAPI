from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from collections import OrderedDict

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def dict(self):
        # Ordered keys: id, username, email
        return OrderedDict([
            ("id", self.id),
            ("username", self.username),
            ("email", self.email)
        ])

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return jsonify({"message": "Welcome to API"})

@app.route('/users', methods=['GET', 'POST', 'DELETE'])
def users():
    if request.method == 'GET':
        users = User.query.all()
        return jsonify({"users": [user.dict() for user in users]})

    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request must be JSON"}), 400

        username = data.get('username')
        email = data.get('email')

        if not username or not email:
            return jsonify({"error": "Missing username or email"}), 400

        # Check uniqueness
        if User.query.filter((User.username == username) | (User.email == email)).first():
            return jsonify({"error": "Username or email already exists"}), 409

        new_user = User(username=username, email=email)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.dict()), 201

    elif request.method == 'DELETE':
        users = User.query.all()
        if not users:
            return jsonify({"message": "No users to delete"}), 404
        for user in users:
            db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "All users have been deleted"}), 200

@app.route('/users/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def user_detail(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    if request.method == 'GET':
        return jsonify(user.dict())

    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request must be JSON"}), 400

        username = data.get('username', user.username)
        email = data.get('email', user.email)

        # Check uniqueness for updated values
        if (username != user.username and User.query.filter_by(username=username).first()) or \
           (email != user.email and User.query.filter_by(email=email).first()):
            return jsonify({"error": "Username or email already exists"}), 409

        user.username = username
        user.email = email
        db.session.commit()
        return jsonify(user.dict())

    elif request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"User {id} deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True)
