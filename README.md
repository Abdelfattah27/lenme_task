# Lenme Loan Management System 

The Lenme Loan Management System is a Django REST project designed to facilitate the loan process between borrowers and investors on the Lenme platform. This system automates the flow of loan requests, offers, acceptance, funding, repayment scheduling, and completion status updates.

## Table of Contents
- [Requirements](#requirements)
- [Project Setup with Poetry](#project-setup-with-poetry)
- [API Endpoints](#api-endpoints)
- [Loan Process](#loan-process)

## Requirements

To run the Lenme Loan Management System, ensure you have the following dependencies installed:
- Python (3.x recommended)
- Poetry

## Project Setup with Poetry

1. Clone the repository to your local machine.
2. Navigate to the project directory using a terminal.
3. Create a virtual environment and install dependencies using Poetry: 
```bash
   poetry install
```
4. Activate the virtual environment:
```bash
poetry shell
```
5. Apply migrations to set up the database:
```bash
python manage.py migrate
```
6. Run the development server:
```bash
python manage.py runserver
```
### API Endpoints

The Lenme Loan Management System exposes the following API endpoints:

- POST /register/: Register a new user.
- GET /loan-requests/: Retrieve all loan requests for the logged-in user.
- POST /loan-requests/: Submit a new loan request.
- GET /loan-offers/: List loan offers for the logged-in investor.
- POST /loan-offers/: Submit a loan offer to a loan request.
- GET /loan-offers/{pk}/accept_offer/: Accept a loan offer and fund the loan.
- GET /loan-offers/{pk}/complete_offer/: Complete a loan offer and the associated loan.

### Loan Process

- Borrower submits a loan request with the desired loan amount and loan period.
- Investor submits an offer with the specified annual interest rate.
- Borrower accepts the offer.
- System checks if the investor has enough balance to fund the total loan amount (loan amount + Lenme fee).
- If the investor's balance is sufficient, the loan is successfully funded, and its status becomes "Funded".
- As payments are successfully made, the outstanding balance decreases.
- Once all payments are completed, the loan status changes to "Completed".