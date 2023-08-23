from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import LoanUser , LoanRequest ,LoanOffer
from .serializers import  LoanRequestSerializer , UserRegistrationSerializer, LoanOfferSerializer , LoanRequestCreateSerializer
from django.db import transaction
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated 
from django.db.models import Q 
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema


def calculate_total_loan_amount(loan_offer):
    loan_request = loan_offer.loan_request
    total_loan_amount = (
        float(loan_request.loan_amount)
        + float(loan_request.loan_amount) * float(loan_offer.annual_interest_rate / 100)
        * float((loan_request.loan_period / 12))
        + 3.00
    )
    return total_loan_amount

class UserRegistrationView(generics.CreateAPIView):
    queryset = LoanUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [] 
    def perform_create(self, serializer):
        user = serializer.save()
        user.set_password(serializer.validated_data['password'])
        user.save()

    @swagger_auto_schema(
        request_body=UserRegistrationSerializer,
        responses={status.HTTP_201_CREATED: 'User registered successfully'},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoanRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated] 
    queryset = LoanRequest.objects.all()
    serializer_class = LoanRequestSerializer

    def list(self, request , *args, **kwargs):
        """
        Retrieve all loan requests for the logged-in user.

        This endpoint retrieves all loan requests associated with the currently logged-in user.
        It includes both pending and non-pending requests.

        Responses:
        - 200 OK: List of loan request objects.
        """
        user = request.user
        requests = LoanRequest.objects.filter(Q(borrower = user)|Q(status="Pending") )

        serializer = LoanRequestSerializer(requests, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Submit a new loan request.

        This endpoint allows the user to submit a new loan request.
        The required fields in the request data are 'loan_amount' and 'loan_period'.

        Responses:
        - 201 Created: Loan request submitted successfully.
        - 400 Bad Request: Invalid request data.
        """
        loan_amount = request.data.get('loan_amount')
        loan_period = request.data.get('loan_period')

        if loan_amount is None or loan_period is None:
            return Response({'message': 'loan_amount and loan_period are required fields'}, status=status.HTTP_400_BAD_REQUEST)

        loan_request_data = {
            'loan_amount': loan_amount,
            'loan_period': loan_period
        }

        serializer = LoanRequestCreateSerializer(data=loan_request_data)
        if serializer.is_valid():
            loan_request = LoanRequest.objects.create(
                borrower=request.user,  # Assuming user authentication
                **loan_request_data
            )
            return Response({'message': 'Loan request submitted successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoanOfferViewSet(viewsets.ModelViewSet):
    queryset = LoanOffer.objects.all()
    serializer_class = LoanOfferSerializer
    permission_classes = [IsAuthenticated]


    def list(self, request , *args, **kwargs):
        """
        List loan offers for the logged-in investor.

        This endpoint retrieves all loan offers made by the logged-in investor.
        It lists the loan offers associated with the investor's account.

        Responses:
        - 200 OK: List of loan offer objects.
        """
        investor = request.user
        borrower_offers = LoanOffer.objects.filter(investor=investor)
        serializer = LoanOfferSerializer(borrower_offers, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='GET',
        responses={
            status.HTTP_200_OK: 'Loan offer accepted and loan funded successfully',
            status.HTTP_400_BAD_REQUEST: 'Invalid request or insufficient balance'
        },
        operation_description="Accept a loan offer and fund the loan.",
    )
    @action(detail=True, methods=['GET'])
    def accept_offer(self, request, pk=None):
        """
        Accept a loan offer and fund the loan.

        This endpoint allows the borrower to accept a pending loan offer and fund the associated loan request.
        If the borrower's balance is sufficient, the loan offer status changes to 'Accepted',
        the investor's balance is updated, and the loan request status changes to 'Funded'.

        Responses:
        - 200 OK: Loan offer accepted and loan funded successfully.
        - 400 Bad Request: Invalid request or insufficient balance.
        """
        borrower = request.user 
        try:
            with transaction.atomic():
                loan_offer = LoanOffer.objects.select_for_update().get(pk=pk, loan_request__borrower=borrower, status='Pending')                
                total_loan_amount = calculate_total_loan_amount(loan_offer)              
                
                if loan_offer.investor.balance < total_loan_amount:
                    return Response({'message': 'Investor does not have sufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

                loan_offer.status = 'Accepted'
                loan_offer.investor.save()
                loan_offer.save()

                loan_request = loan_offer.loan_request
                loan_request.status = 'Funded'
                loan_request.save()

        except LoanOffer.DoesNotExist:
            return Response({'message': 'Loan offer not found or not in Pending status'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'message': 'Loan offer accepted and loan funded successfully'}, status=status.HTTP_200_OK)
    
    
    @swagger_auto_schema(
        method='GET',
        responses={
            status.HTTP_200_OK: 'Loan offer completed and loan completed successfully',
            status.HTTP_400_BAD_REQUEST: 'Invalid request or insufficient balance'
        },
        operation_description="Complete a loan offer and the associated loan.",
    )
    @action(detail=True, methods=['GET'])
    def complete_offer(self, request, pk=None):
        """
        Complete a loan offer and the associated loan.

        This endpoint allows the investor to complete an accepted loan offer.
        If the investor's balance is sufficient, the loan offer status changes to 'Completed',
        the investor's balance is updated, and the loan request status changes to 'Completed'.

        Responses:
        - 200 OK: Loan offer completed and loan completed successfully.
        - 400 Bad Request: Invalid request or insufficient balance.
        """
        investor = request.user 
        try:
            with transaction.atomic():
                loan_offer = LoanOffer.objects.select_for_update().get(pk=pk, investor=investor, status='Accepted')  
                total_loan_amount = calculate_total_loan_amount(loan_offer)              

                if loan_offer.investor.balance < total_loan_amount:
                    return Response({'message': 'Investor does not have sufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

                loan_offer.status = 'Completed'
                loan_offer.investor.balance =float(loan_offer.investor.balance) -  total_loan_amount
                loan_offer.investor.save()
                loan_offer.save()

                loan_request = loan_offer.loan_request
                loan_request.status = 'Completed'
                loan_request.save()

        except LoanOffer.DoesNotExist:
            return Response({'message': 'Loan offer not found or not in Pending status'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'message': 'Loan offer Completed and loan Completed successfully'}, status=status.HTTP_200_OK)

   
    

    def create(self, request, *args, **kwargs):
        investor = request.user  
        loan_request_id = request.data.get('loan_request')
        annual_interest_rate = request.data.get('annual_interest_rate')

        if loan_request_id is None or annual_interest_rate is None:
            return Response({'message': 'loan_request_id and annual_interest_rate are required fields'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            loan_request = LoanRequest.objects.get(pk=loan_request_id, status='Pending')
        except LoanRequest.DoesNotExist:
            return Response({'message': 'Loan request not found or not in Pending status'}, status=status.HTTP_400_BAD_REQUEST)

        if loan_request.borrower == request.user : 
            return Response({'message': "You can't make an offer to yourself"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        LoanOffer.objects.create(
            investor=investor,
            loan_request=loan_request,
            annual_interest_rate=annual_interest_rate
        )


        return Response({'message': 'Loan offer submitted successfully'}, status=status.HTTP_201_CREATED)

