from rest_framework import serializers
from .models import LoanRequest, LoanOffer , LoanUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanUser
        fields = ['username', 'email', 'password' , "balance"]
        extra_kwargs = {'password': {'write_only': True}}


class LoanRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRequest
        fields = ['loan_amount', 'loan_period']

class LoanRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRequest
        fields = '__all__'



class LoanOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanOffer
        fields = ['annual_interest_rate' , "loan_request"]
