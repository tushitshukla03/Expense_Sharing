from django.urls import path
from .views import (
    GetBalance, UserCreateView, UserDetailView, 
    ExpenseCreateView, ExpenseDetailView, GetExpenseSplit,
    UserExpensesView, OverallExpensesView, DownloadBalanceSheetView
)
urlpatterns = [
    path('users/create/', UserCreateView.as_view(), name='user-create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('expenses/create/', ExpenseCreateView.as_view(), name='expense-create'),
    path('expenses/', ExpenseDetailView.as_view(), name='expense-detail'),
    path('expenses/split/<int:expense_id>/', GetExpenseSplit.as_view(), name='expense-split'),
    path('balances/<int:user_id>/', GetBalance.as_view(), name='get-balance'),
    path('users/<int:user_id>/expenses/', UserExpensesView.as_view(), name='user-expenses'),
    path('expenses/overall/', OverallExpensesView.as_view(), name='overall-expenses'),
    path('balances/download/', DownloadBalanceSheetView.as_view(), name='download-balance-sheet'),
]
