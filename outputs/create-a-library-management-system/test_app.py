import pytest
from datetime import date, timedelta
from app import Book, Member, Loan, db

# Helper function to seed the database with initial data
def seed_db():
    book1 = Book(Title="Book One", Author="Author1", ISBN="ISBN1234567890", Genre="Fantasy", QuantityAvailable=5)
    member1 = Member(Name="Member1", Address="Address1", ContactNumber="Contact1")
    db.session.add_all([book1, member1])
    db.session.commit()

@pytest.fixture(scope='module')
def client():
    # Reset database
    db.drop_all()
    db.create_all()
    seed_db()
    
    test_app = app.test_client()
    context = app.app_context()
    context.push()
    yield test_app  # This is where the testing happens!
    context.pop()

@pytest.mark.usefixtures('client')
class TestBookOperations:
    def test_add_book(self, client):
        response = client.post('/api/books', json={
            "Title": "New Book",
            "Author": "New Author",
            "ISBN": "1234567890123",
            "Genre": "Science Fiction",
            "QuantityAvailable": 3
        })
        assert response.status_code == 201
        assert response.json["Message"] == "Book added successfully"

    def test_get_book(self, client):
        response = client.get('/api/books/1')
        assert response.status_code == 200
        assert response.json["StatusCode"] == 200

    def test_update_book(self, client):
        response = client.put('/api/books/1', json={
            "Title": "Updated Title"
        })
        assert response.status_code == 200
        assert response.json["Message"] == "Book updated successfully"

    def test_delete_book(self, client):
        response = client.delete('/api/books/1')
        assert response.status_code == 200
        assert response.json["Message"] == "Book removed successfully"

@pytest.mark.usefixtures('client')
class TestMemberOperations:
    def test_register_member(self, client):
        response = client.post('/api/members', json={
            "Name": "New Member",
            "Address": "New Address",
            "ContactNumber": "New Contact"
        })
        assert response.status_code == 201
        assert response.json["Message"] == "Member registered successfully"

    def test_get_member(self, client):
        response = client.get('/api/members/1')
        assert response.status_code == 200
        assert response.json["StatusCode"] == 200

    def test_update_member(self, client):
        response = client.put('/api/members/1', json={
            "Name": "Updated Name"
        })
        assert response.status_code == 200
        assert response.json["Message"] == "Member updated successfully"

    def test_delete_member(self, client):
        response = client.delete('/api/members/1')
        assert response.status_code == 200
        assert response.json["Message"] == "Member account deleted successfully"

@pytest.mark.usefixtures('client')
class TestLoanOperations:
    def test_issue_book(self, client):
        response = client.post('/api/loans', json={
            "BookID": 1,
            "MembershipID": 1,
            "DateBorrowed": str(date.today().isoformat())
        })
        assert response.status_code == 200
        assert response.json["Message"] == "Book issued successfully"

    def test_return_book(self, client):
        date_borrowed = date.today() - timedelta(days=16)
        due_date = date_borrowed + timedelta(days=15)
        late_fee = (date.today() - due_date).days * 0.5
        response = client.put('/api/loans/1', json={"DateReturned": str(date.today())})
        assert response.status_code == 200
        assert response.json["Message"] == "Book returned successfully"
        assert round(response.json["LateFee"], 2) == late_fee

@pytest.mark.usefixtures('client')
class TestReports:
    def test_book_availability_report(self, client):
        response = client.get('/api/reports/availability')
        assert response.status_code == 200
        assert response.json["StatusCode"] == 200
        assert len(response.json["Data"]) > 0

    def test_library_usage_report(self, client):
        response = client.get('/api/reports/usage')
        assert response.status_code == 200
        assert response.json["StatusCode"] == 200
        assert len(response.json["Data"]) > 0

    def test_overdue_fines_report(self, client):
        loan = Loan(BookID=1, MembershipID=1, DateBorrowed=date.today() - timedelta(days=46))
        db.session.add(loan)
        db.session.commit()

        response = client.get('/api/reports/overdue')
        assert response.status_code == 200
        assert response.json["StatusCode"] == 200
        assert len(response.json["Data"]) > 0

# Error cases (assuming a custom error handler is in place that returns error messages)
@pytest.mark.usefixtures('client')
class TestErrorHandling:
    def test_book_not_found(self, client):
        response = client.get('/api/books/999')
        assert response.status_code == 404
        assert "Book not found" in response.json["error"]

    def test_member_not_found(self, client):
        response = client.get('/api/members/999')
        assert response.status_code == 404
        assert "Member not found" in response.json["error"]

    def test_loan_not_found(self, client):
        response = client.put('/api/loans/999', json={"DateReturned": str(date.today())})
        assert response.status_code == 404
        assert "Loan not found" in response.json["error"]

    def test_invalid_book_data(self, client):
        response = client.post('/api/books', json={
            "Title": "",
            "Author": "Author1",
            "ISBN": "1234567890",
            "Genre": "Fantasy",
            "QuantityAvailable": -1
        })
        assert response.status_code == 422
        assert "Invalid input" in response.json["error"]