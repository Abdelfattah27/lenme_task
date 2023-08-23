from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import LoanUser , LoanRequest, LoanOffer
from django.urls import reverse

class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        registration_data = {
            'username': 'newuser',
            'password': 'testpassword',
            'email': 'newuser@example.com',
            'balance': 1000.00
        }
        response = self.client.post('/api/register/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_duplicate_user_registration(self):
        existing_user = LoanUser.objects.create_user(username='abdelfatah273', password='testpassword')
        registration_data = {
            'username': 'abdelfatah273',
            'password': 'testpassword',
            'email': 'anotheruser@example.com',
            'balance': 2000.00
        }
        response = self.client.post('/api/register/', registration_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)





class LoanRequestTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = LoanUser.objects.create_user(username='testuser', password='testpassword')

    def test_borrower_submits_loan_request(self):
        self.client.force_authenticate(user=self.user)

        loan_request_data = {
            'loan_amount': 5000.00,
            'loan_period': 6
        }

        response = self.client.post('/api/loan-requests/', loan_request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify that the loan request is created with the correct data
        loan_request = LoanRequest.objects.get(borrower=self.user)
        self.assertEqual(loan_request.loan_amount, loan_request_data['loan_amount'])
        self.assertEqual(loan_request.loan_period, loan_request_data['loan_period'])




class LoanOfferTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.borrower = LoanUser.objects.create_user(username='borrower', password='testpassword')
        self.investor = LoanUser.objects.create_user(username='investor', password='testpassword')

    def test_investor_submits_loan_offer(self):
        self.client.force_authenticate(user=self.investor)

        loan_request = LoanRequest.objects.create(borrower=self.borrower, loan_amount=5000.00, loan_period=6)

        loan_offer_data = {
            'loan_request': loan_request.id,
            'annual_interest_rate': 15.0
        }

        response = self.client.post('/api/loan-offers/', loan_offer_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify that the loan offer is created with the correct data
        loan_offer = LoanOffer.objects.get(investor=self.investor)
        self.assertEqual(loan_offer.loan_request, loan_request)
        self.assertEqual(loan_offer.annual_interest_rate, loan_offer_data['annual_interest_rate'])




class LoanOfferAcceptanceTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.borrower = LoanUser.objects.create_user(username='borrower', password='testpassword')
        self.investor_with_balance = LoanUser.objects.create_user(username='investor1', password='testpassword', balance=10000.00)
        self.investor_without_balance = LoanUser.objects.create_user(username='investor2', password='testpassword', balance=100.00)

    def test_borrower_accepts_loan_offer_with_sufficient_balance(self):
        self.client.force_authenticate(user=self.borrower)

        loan_request = LoanRequest.objects.create(borrower=self.borrower, loan_amount=5000.00, loan_period=6)
        loan_offer = LoanOffer.objects.create(investor=self.investor_with_balance, loan_request=loan_request, annual_interest_rate=15.0)

        response = self.client.get(f'/api/loan-offers/{loan_offer.id}/accept_offer/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the loan offer and loan request statuses are updated
        loan_offer.refresh_from_db()
        self.assertEqual(loan_offer.status, 'Accepted')
        loan_request.refresh_from_db()
        self.assertEqual(loan_request.status, 'Funded')

    def test_borrower_accepts_loan_offer_with_insufficient_balance(self):
        self.client.force_authenticate(user=self.borrower)

        loan_request = LoanRequest.objects.create(borrower=self.borrower, loan_amount=5000.00, loan_period=6)
        loan_offer = LoanOffer.objects.create(investor=self.investor_without_balance, loan_request=loan_request, annual_interest_rate=15.0)

        response = self.client.get(f'/api/loan-offers/{loan_offer.id}/accept_offer/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Investor does not have sufficient balance')



class LoanOfferCompletionTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.borrower = LoanUser.objects.create_user(username='borrower', password='testpassword')
        self.investor_with_balance = LoanUser.objects.create_user(username='investor1', password='testpassword', balance=10000.00)
        self.investor_without_balance = LoanUser.objects.create_user(username='investor2', password='testpassword', balance=100.00)

    def test_investor_completes_loan_offer_with_sufficient_balance(self):
        self.client.force_authenticate(user=self.investor_with_balance)
        loan_request = LoanRequest.objects.create(borrower=self.borrower, loan_amount=5000.00, loan_period=6)
        loan_offer = LoanOffer.objects.create(investor=self.investor_with_balance, loan_request=loan_request, annual_interest_rate=15.0, status='Accepted')

        response = self.client.get(reverse('loanoffer-complete-offer', args=[loan_offer.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Loan offer Completed and loan Completed successfully')

        # Verify that the loan offer and loan request statuses are updated
        loan_offer.refresh_from_db()
        self.assertEqual(loan_offer.status, 'Completed')
        loan_request.refresh_from_db()
        self.assertEqual(loan_request.status, 'Completed')
        investor = LoanUser.objects.get(username=self.investor_with_balance.username)
        self.assertEqual(float(investor.balance), 10000.00 - float(float(loan_request.loan_amount) + float(loan_request.loan_amount) * float(loan_offer.annual_interest_rate/100) * (loan_request.loan_period / 12) + 3.00))
    def test_investor_completes_loan_offer_with_insufficient_balance(self):
        self.client.force_authenticate(user=self.investor_without_balance)
        loan_request = LoanRequest.objects.create(borrower=self.borrower, loan_amount=5000.00, loan_period=6)
        loan_offer = LoanOffer.objects.create(investor=self.investor_without_balance, loan_request=loan_request, annual_interest_rate=15.0, status='Accepted')

        response = self.client.get(reverse('loanoffer-complete-offer', args=[loan_offer.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Investor does not have sufficient balance')

        # Verify that the loan offer and loan request statuses are not updated
        loan_offer.refresh_from_db()
        self.assertEqual(loan_offer.status, 'Accepted')
        loan_request.refresh_from_db()
        self.assertEqual(loan_request.status, 'Pending')
        investor = LoanUser.objects.get(username=self.investor_without_balance.username)
        self.assertEqual(float(investor.balance), 100.00)  # Balance remains the same



class LoanOfferCreationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.borrower = LoanUser.objects.create_user(username='borrower', password='testpassword')
        self.investor = LoanUser.objects.create_user(username='investor', password='testpassword')
        self.loan_request = LoanRequest.objects.create(borrower=self.borrower, loan_amount=5000.00, loan_period=6)

    def test_create_loan_offer(self):
        self.client.force_authenticate(user=self.investor)

        data = {
            'loan_request': self.loan_request.id,
            'annual_interest_rate': 15.0
        }

        response = self.client.post(reverse('loanoffer-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Loan offer submitted successfully')

        # Verify that the loan offer is created with the correct data
        loan_offer = LoanOffer.objects.get(investor=self.investor, loan_request=self.loan_request)
        self.assertEqual(loan_offer.annual_interest_rate, 15.0)
        self.assertEqual(loan_offer.status, 'Pending')

    def test_create_loan_offer_invalid_data(self):
        self.client.force_authenticate(user=self.investor)

        # Missing loan_request_id and annual_interest_rate
        data = {}

        response = self.client.post(reverse('loanoffer-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'loan_request_id and annual_interest_rate are required fields')

    def test_create_loan_offer_invalid_loan_request_status(self):
        self.client.force_authenticate(user=self.investor)

        # Change loan request status to 'Completed'
        self.loan_request.status = 'Completed'
        self.loan_request.save()

        data = {
            'loan_request': self.loan_request.id,
            'annual_interest_rate': 15.0
        }

        response = self.client.post(reverse('loanoffer-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Loan request not found or not in Pending status')

    def test_create_loan_offer_to_self(self):
        self.client.force_authenticate(user=self.borrower)

        data = {
            'loan_request': self.loan_request.id,
            'annual_interest_rate': 15.0
        }

        response = self.client.post(reverse('loanoffer-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "You can't make an offer to yourself")




