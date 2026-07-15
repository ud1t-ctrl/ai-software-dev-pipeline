CREATE TABLE Book (
    BookID INT PRIMARY KEY IDENTITY(1,1),
    Title NVARCHAR(255) NOT NULL,
    Author NVARCHAR(255) NOT NULL,
    ISBN NVARCHAR(13) UNIQUE NOT NULL,
    Genre NVARCHAR(100),
    QuantityAvailable INT NOT NULL
);

CREATE TABLE Member (
    MembershipID INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(255) NOT NULL,
    Address NVARCHAR(255),
    ContactNumber NVARCHAR(15)
);

CREATE TABLE Loan (
    LoanID INT PRIMARY KEY IDENTITY(1,1),
    BookID INT,
    MembershipID INT,
    DateBorrowed DATE NOT NULL,
    DueDate DATE NOT NULL,
    DateReturned DATE,
    FOREIGN KEY (BookID) REFERENCES Book(BookID),
    FOREIGN KEY (MembershipID) REFERENCES Member(MembershipID)
);