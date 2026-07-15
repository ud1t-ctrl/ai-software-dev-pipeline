from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db = SQLAlchemy(app)
CORS(app)

class Book(db.Model):
    BookID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(255), nullable=False)
    Author = db.Column(db.String(255), nullable=False)
    ISBN = db.Column(db.String(13), unique=True, nullable=False)
    Genre = db.Column(db.String(100))
    QuantityAvailable = db.Column(db.Integer, nullable=False)

class Member(db.Model):
    MembershipID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(255), nullable=False)
    Address = db.Column(db.String(255))
    ContactNumber = db.Column(db.String(15))

class Loan(db.Model):
    LoanID = db.Column(db.Integer, primary_key=True)
    BookID = db.Column(db.Integer, db.ForeignKey('book.BookID'), nullable=False)
    MembershipID = db.Column(db.Integer, db.ForeignKey('member.MembershipID'), nullable=False)
    DateBorrowed = db.Column(db.Date, nullable=False)
    DueDate = db.Column(db.Date, nullable=False)
    DateReturned = db.Column(db.Date)

@app.route('/api/books', methods=['POST'])

@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.get_json()

    required_fields = ['Title', 'Author', 'ISBN', 'Genre', 'QuantityAvailable']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}), 400

    book = Book(Title=data['Title'], Author=data['Author'], ISBN=data['ISBN'], Genre=data['Genre'], QuantityAvailable=data['QuantityAvailable'])
    db.session.add(book)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": f"A book with ISBN '{data['ISBN']}' already exists"}), 409

    return jsonify({"StatusCode": 201, "Message": "Book added successfully"}), 201
   
@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    return json_response({"StatusCode": 200, "Data": book.to_dict()})

@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    book = Book.query.get_or_404(book_id)
    for key, value in data.items():
        setattr(book, key, value)
    db.session.commit()
    return jsonify({"StatusCode": 200, "Message": "Book updated successfully"})

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return jsonify({"StatusCode": 200, "Message": "Book removed successfully"})

@app.route('/api/members', methods=['POST'])
def register_member():
    data = request.get_json()
    member = Member(Name=data['Name'], Address=data['Address'], ContactNumber=data['ContactNumber'])
    db.session.add(member)
    db.session.commit()
    return jsonify({"StatusCode": 201, "Message": "Member registered successfully", "MembershipID": member.MembershipID})

@app.route('/api/members/<int:membership_id>', methods=['GET'])
def get_member(membership_id):
    member = Member.query.get_or_404(membership_id)
    return json_response({"StatusCode": 200, "Data": member.to_dict()})

@app.route('/api/members/<int:membership_id>', methods=['PUT'])
def update_member(membership_id):
    data = request.get_json()
    member = Member.query.get_or_404(membership_id)
    for key, value in data.items():
        setattr(member, key, value)
    db.session.commit()
    return jsonify({"StatusCode": 200, "Message": "Member updated successfully"})

@app.route('/api/members/<int:membership_id>', methods=['DELETE'])
def delete_member(membership_id):
    member = Member.query.get_or_404(membership_id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({"StatusCode": 200, "Message": "Member account deleted successfully"})

from datetime import datetime, timedelta, date

@app.route('/api/loans', methods=['POST'])
def issue_book():
    data = request.get_json()
    try:
        borrowed_date = datetime.strptime(data['DateBorrowed'], '%Y-%m-%d').date()
    except (KeyError, ValueError):
        return jsonify({"error": "DateBorrowed is required in YYYY-MM-DD format"}), 400

    due_date = borrowed_date + timedelta(days=15)

    loan = Loan(
        BookID=data['BookID'],
        MembershipID=data['MembershipID'],
        DateBorrowed=borrowed_date,
        DueDate=due_date
    )
    db.session.add(loan)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Invalid BookID or MembershipID"}), 400

    return jsonify({"StatusCode": 200, "Message": "Book issued successfully", "DueDate": str(due_date)}), 200


@app.route('/api/loans/<int:loan_id>', methods=['PUT'])
def return_book(loan_id):
    data = request.get_json()
    loan = Loan.query.get_or_404(loan_id)

    return_date_str = data.get('DateReturned')
    if not return_date_str:
        return jsonify({"error": "DateReturned is required"}), 400
    try:
        return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "DateReturned must be in YYYY-MM-DD format"}), 400

    late_fee = calculate_late_fee(loan.DueDate, return_date)
    loan.DateReturned = return_date
    db.session.commit()
    return jsonify({"StatusCode": 200, "Message": "Book returned successfully", "LateFee": late_fee})


def calculate_late_fee(due_date, return_date):
    days_overdue = max(0, (return_date - due_date).days)
    return days_overdue * 0.5
@app.route('/api/reports/availability', methods=['GET'])
def book_availability_report():
    books = Book.query.all()
    availability = [{'BookID': book.BookID, 'Title': book.Title, 'Available': book.QuantityAvailable > 0} for book in books]
    return json_response({"StatusCode": 200, "Data": availability})

@app.route('/api/reports/usage', methods=['GET'])
def library_usage_report():
    member_books = db.session.query(Member.MembershipID, Member.Name, func.count(Loan.LoanID).label('BooksBorrowedCount')).join(Loan, Member.MembershipID == Loan.MembershipID).group_by(Member.MembershipID)
    return json_response({"StatusCode": 200, "Data": [{"MemberID": row.MembershipID, "Name": row.Name, "BooksBorrowedCount": row.BooksBorrowedCount} for row in member_books]})

@app.route('/api/reports/overdue', methods=['GET'])
def overdue_fines_report():
    loans = Loan.query.filter(Loan.DateReturned == None).all()
    fines = [{'LoanID': loan.LoanID, 'BookID': loan.BookID, 'MembershipID': loan.MembershipID, 'DateBorrowed': str(loan.DateBorrowed), 'DueDate': str(loan.DueDate), 'FineAmount': calculate_late_fee(loan.DateBorrowed)} for loan in loans]
    return json_response({"StatusCode": 200, "Data": fines})

def json_response(data):
    from flask import jsonify
    response = jsonify(data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)