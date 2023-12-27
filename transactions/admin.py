from django.contrib import admin
from transactions.models import Transaction
from transactions.views import send_transaction_email

# Register your models here.
@admin.register(Transaction)

class TransactionsAdmin(admin.ModelAdmin):
    list_display = ['account', 'amount', 'balance_after_transaction', 'transaction_type', 'loan_approved']

    def save_model(self, request, obj, form, change):
        if obj.loan_approved == True:
            obj.account.balance += obj.amount
            obj.balance_after_transaction = obj.account.balance
            obj.account.save()
            send_transaction_email('transactions/email_template.html', 'Loan Approval', obj.account.user, obj.amount, 'Loan Approval Success Message')
        return super().save_model(request, obj, form, change)


