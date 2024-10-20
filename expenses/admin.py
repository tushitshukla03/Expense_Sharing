from django.contrib import admin
from .models import Expense

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('payer', 'amount', 'split_method')
    filter_horizontal = ('participants',)  

admin.site.register(Expense, ExpenseAdmin)