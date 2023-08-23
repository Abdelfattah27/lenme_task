from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class LoanUser(AbstractUser):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.username


class LoanRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
    ]
    borrower = models.ForeignKey(LoanUser, on_delete=models.CASCADE, null=True, blank=True)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    loan_period = models.PositiveIntegerField()  # In months
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.borrower.username} - Amount: {self.loan_amount} - Period: {self.loan_period} months"

    class Meta:
        db_table = 'loan_request'


class LoanOffer(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Funded', 'Funded'),
        ('Completed', 'Completed'),
    ]
    investor = models.ForeignKey(LoanUser, on_delete=models.CASCADE)
    loan_request = models.ForeignKey(LoanRequest, on_delete=models.CASCADE)
    annual_interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Investor: {self.investor.username} - Loan Request: {self.loan_request.id} - Status: {self.status}"

    def clean(self):
        if not (0 <= self.annual_interest_rate <= 100):
            raise ValidationError('Annual interest rate must be between 0 and 100.')

    class Meta:
        db_table = 'loan_offer'
