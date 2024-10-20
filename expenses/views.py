from rest_framework import generics
from .models import User , Expense
from .serializers import UserSerializer, ExpenseSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models
from rest_framework import  status
from .models import Balance
from django.http import HttpResponse
import csv
from django.db import transaction  

import logging

class GetBalance(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        balances = Balance.objects.filter(from_user=user)

        balance_data = [
            {
                "to_user": balance.to_user.name,  
                "amount": balance.amount
            }
            for balance in balances
        ]
        
        return Response(balance_data)





logger = logging.getLogger(__name__)

class UserExpensesView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            paid_expenses = Expense.objects.filter(payer=user)
            participated_expenses = Expense.objects.filter(participants=user)
            
            paid_data = ExpenseSerializer(paid_expenses, many=True).data
            participated_data = ExpenseSerializer(participated_expenses, many=True).data
            
            response_data = {
                "paid_expenses": paid_data,
                "participated_expenses": participated_data,
                "total_paid": sum(expense.amount for expense in paid_expenses),
                "total_participated": sum(expense.amount for expense in participated_expenses)
            }
            
            return Response(response_data)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

class OverallExpensesView(APIView):
    def get(self, request):
        expenses = Expense.objects.all()
        total_amount = sum(expense.amount for expense in expenses)
        
        users = User.objects.all()
        user_summaries = []
        
        for user in users:
            paid = Expense.objects.filter(payer=user)
            participated = Expense.objects.filter(participants=user)
            
            user_summary = {
                "user_id": user.id,
                "name": user.name,
                "total_paid": sum(expense.amount for expense in paid),
                "total_participated": sum(expense.amount for expense in participated)
            }
            user_summaries.append(user_summary)
        
        response_data = {
            "total_expenses": total_amount,
            "expense_count": expenses.count(),
            "user_summaries": user_summaries,
            "recent_expenses": ExpenseSerializer(expenses.order_by('-id')[:5], many=True).data
        }
        
        return Response(response_data)

# views.py
class DownloadBalanceSheetView(APIView):
    def get(self, request):
        try:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="balance_sheet.csv"'
            
            writer = csv.writer(response)
            
            writer.writerow([
                'User', 
                'Owes To', 
                'Amount', 
                'Total Paid', 
                'Total Participated In',
                'Net Balance'
            ])
            
            users = User.objects.all()
            
            for user in users:
                owes = Balance.objects.filter(from_user=user)
                owed = Balance.objects.filter(to_user=user)
                
                total_paid = Expense.objects.filter(payer=user).aggregate(
                    total=models.Sum('amount'))['total'] or 0
                total_participated = Expense.objects.filter(
                    participants=user).aggregate(total=models.Sum('amount'))['total'] or 0
                
                if owes.exists() or owed.exists():
                    for balance in owes:
                        writer.writerow([
                            balance.from_user.name,
                            balance.to_user.name,
                            f"-{balance.amount}", 
                            total_paid,
                            total_participated,
                            total_paid - total_participated
                        ])
                    
                    for balance in owed:
                        writer.writerow([
                            balance.to_user.name,
                            f"(Owed by {balance.from_user.name})",
                            balance.amount, 
                            total_paid,
                            total_participated,
                            total_paid - total_participated
                        ])
                else:
                    writer.writerow([
                        user.name,
                        "No outstanding balances",
                        "0",
                        total_paid,
                        total_participated,
                        total_paid - total_participated
                    ])
                
                writer.writerow([])
            
            writer.writerow(["SUMMARY"])
            writer.writerow(["Total Expenses", 
                           Expense.objects.aggregate(
                               total= models.Sum('amount'))['total'] or 0])
            writer.writerow(["Number of Expenses", 
                           Expense.objects.count()])
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating balance sheet: {str(e)}")
            return Response(
                {"error": "Failed to generate balance sheet"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
# User Views
class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Expense Views
logger = logging.getLogger(__name__)

class ExpenseCreateView(generics.CreateAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def create(self, request, *args, **kwargs):
        logger.info(f"Received expense creation request with data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                # Start transaction
                with transaction.atomic():
                    expense = serializer.save()
                    logger.info(f"Expense created with ID: {expense.id}")
                    expense.split_expense()
                    logger.info("Expense split successfully")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creating expense: {str(e)}")
                return Response(
                    {"error": str(e), "detail": "Failed to create expense. Please check the user IDs and try again."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        logger.error(f"Serializer validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExpenseDetailView(generics.ListAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

class GetExpenseSplit(APIView):
    def get(self, request, expense_id):
        try:
            expense = Expense.objects.get(id=expense_id)
        except Expense.DoesNotExist:
            return Response({"error": "Expense not found"}, status=404)
        
        split_data = expense.split_expense()
        return Response(split_data)
