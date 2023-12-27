from django import forms 
from transactions.models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type']

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()
    
class DepositForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        min_deposit_amount = 100
        if amount < min_deposit_amount:
            raise forms.ValidationError(f'you can not deposit less than {min_deposit_amount} tk.')
        return amount
    
class withdrawForm(TransactionForm):
    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 100
        max_withdraw_amount = 20000
        amount = self.cleaned_data.get('amount')
        balance = account.balance

        if amount < min_withdraw_amount:
            raise forms.ValidationError(f'you have to withdraw at least {min_withdraw_amount} tk.')
        
        if amount > max_withdraw_amount:
            raise forms.ValidationError(f'you can not withdraw more than {max_withdraw_amount} tk.')
        
        if amount > balance:
            raise forms.ValidationError(f'your balance is too low. you can not withdraw {amount} tk.')
        return amount
    
class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        account = self.account
        balance = account.balance
        loan_amount = self.cleaned_data.get('amount')

        if balance * balance <= loan_amount:
            raise forms.ValidationError(f'you can not loan {loan_amount} tk due to your current balance is {balance} tk. you can loan at most {balance*balance} tk.')
        return loan_amount