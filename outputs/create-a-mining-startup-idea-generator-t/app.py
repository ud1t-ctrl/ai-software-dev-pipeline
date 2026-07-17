from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import jwt
import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db = SQLAlchemy(app)

class User(db.Model):
    UserId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    CreatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    UpdatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class MiningSite(db.Model):
    __tablename__ = 'miningsite'  # Table name is explicitly 'miningsite'
    SiteId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Location = db.Column(db.String(255), nullable=False)
    MineralType = db.Column(db.String(100))
    DepositSize = db.Column(db.DECIMAL(18, 2))
    EstimatedProductionCapacity = db.Column(db.DECIMAL(18, 2))
    ExplorationStatus = db.Column(db.Enum('Exploring', 'Discovered', 'Developed'), default='Exploring')
    CreatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    UpdatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class StartupIdea(db.Model):
    IdeaId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Title = db.Column(db.String(255), nullable=False)
    Description = db.Column(db.Text, nullable=False)
    RelatedMineralType = db.Column(db.String(100))
    FeasibilityScore = db.Column(db.Integer, db.CheckConstraint('FeasibilityScore >= 0 AND FeasibilityScore <= 100'))
    EstimatedCost = db.Column(db.DECIMAL(18, 2))
    # FIXED: Changed 'mining_site.SiteId' to 'miningsite.SiteId' to match the explicit __tablename__ above
    LinkedMiningSiteId = db.Column(db.Integer, db.ForeignKey('miningsite.SiteId'))
    CreatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    UpdatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class UserFavorite(db.Model):
    FavoriteId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserId = db.Column(db.Integer, db.ForeignKey('user.UserId'), nullable=False)
    IdeaId = db.Column(db.Integer, unique=True, nullable=False)
    CreatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    __table_args__ = (
        db.UniqueConstraint('UserId', 'IdeaId', name='user_favorite_constraint'),
    )

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 1. Check if user already exists
    existing_user = User.query.filter_by(Email=data['email']).first()
    if existing_user:
        return make_response(jsonify({'message': 'User already exists'}), 409)

    # 2. If not, create the user
    user = User(Name=data['name'], Email=data['email'])
    db.session.add(user)
    db.session.commit()
    
    token = jwt.encode({'userId': user.UserId, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'], algorithm='HS256')
    
    # Note: If using PyJWT 2.0+, jwt.encode returns a string, not bytes. 
    # If it returns bytes in your setup, you might need token.decode('utf-8')
    return jsonify({'userId': user.UserId, 'token': token}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(Email=data['email']).first()
    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    token = jwt.encode({'userId': user.UserId, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({'userId': user.UserId, 'token': token}), 200

@app.route('/miningsites', methods=['POST'])
def create_mining_site():
    data = request.get_json()
    mining_site = MiningSite(Location=data['location'], MineralType=data['mineralType'], DepositSize=data['depositSize'], EstimatedProductionCapacity=data['estimatedProductionCapacity'], ExplorationStatus=data['explorationStatus'])
    db.session.add(mining_site)
    db.session.commit()
    return jsonify({'siteId': mining_site.SiteId, **data}), 201

@app.route('/miningsites/<int:site_id>', methods=['PUT'])
def update_mining_site(site_id):
    data = request.get_json()
    mining_site = MiningSite.query.filter_by(SiteId=site_id).first()
    if not mining_site:
        return make_response('Mining site not found', 404)
    for key, value in data.items():
        setattr(mining_site, key, value)
    db.session.commit()
    return jsonify({**data}), 200

@app.route('/miningsites/<int:site_id>', methods=['DELETE'])
def delete_mining_site(site_id):
    mining_site = MiningSite.query.filter_by(SiteId=site_id).first()
    if not mining_site:
        return make_response('Mining site not found', 404)
    db.session.delete(mining_site)
    db.session.commit()
    return '', 204

@app.route('/startupideas/miningsite/<int:mining_site_id>', methods=['GET'])
def generate_startup_idea(mining_site_id):
    mining_site = MiningSite.query.filter_by(SiteId=mining_site_id).first()
    if not mining_site:
        return make_response('Mining site not found', 404)
    idea = StartupIdea(Title=f"Miner Gold Exploration Project", LinkedMiningSiteId=mining_site_id)
    db.session.add(idea)
    db.session.commit()
    return jsonify({**idea.__dict__}), 200

@app.route('/favorites', methods=['POST'])
def save_startup_idea():
    data = request.get_json()
    favorite = UserFavorite(UserId=data['userId'], IdeaId=data['ideaId'])
    if UserFavorite.query.filter_by(IdeaId=favorite.IdeaId).first():
        return make_response('Startup idea already favorited', 409)
    db.session.add(favorite)
    db.session.commit()
    return '', 201

@app.route('/favorites/<int:favor_id>', methods=['DELETE'])
def remove_startup_idea(favor_id):
    favorite = UserFavorite.query.filter_by(FavoriteId=favor_id).first()
    if not favorite:
        return make_response('Favorite not found', 404)
    db.session.delete(favorite)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Adding app.run so the server actually launches when executed directly
    app.run(debug=True)