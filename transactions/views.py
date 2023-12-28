from django.http import HttpResponse,Http404
from django.contrib import messages
from django.db.models import Sum
from django.urls import reverse_lazy
from django.shortcuts import redirect,get_object_or_404
from django.views.generic import CreateView,ListView,FormView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from transactions.models import Transaction
from .constants import DEPOSIT,WITHDRAWAL,LOAN,LOAN_PAID,SEND_MONEY,RECEIVED_MONEY
from transactions.forms import withdrawForm,DepositForm,LoanRequestForm,TransferMoneyForm
from datetime import datetime
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from accounts.models import UserBankAccount

############# Transaction Email Send Start ############

def send_transaction_email(template, transaction_type, user, amount, mail_subject):
    message = render_to_string(template, {
        'user': user,
        'amount': amount,
        'type' : transaction_type
    })
    from_email = "Mamar Bank <delwarjnu24@gmail.com>"
    send_email = EmailMultiAlternatives(mail_subject, '', to=[user.email], from_email=from_email, reply_to=[from_email])
    send_email.attach_alternative(message, 'text/html')
    send_email.send()

############# Transaction Email Send End ############

# Create your views here.
class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    title = ''
    model = Transaction
    success_url = reverse_lazy('transaction_report')


    def get_form_kwargs(self,**kwargs):
        form_kwargs = super().get_form_kwargs(**kwargs)
        form_kwargs.update({
            'account': self.request.user.account
        })
        return form_kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title
        })
        return context
    
class DepositMoneyView(TransactionCreateMixin):
    title = 'Deposit'
    form_class = DepositForm

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial
    
    def form_valid(self, form):
        account = self.request.user.account
        amount = form.cleaned_data.get('amount')
        account.balance += amount
        account.save(update_fields = ['balance'])
        messages.success(self.request, f'{amount} tk was deposited in your account successfully')
        send_transaction_email('transactions/email_template.html', 'Deposite', self.request.user, amount, 'Deposit Success Message')
        return super().form_valid(form)
    
class WithdrawMoneyView(TransactionCreateMixin):
    title = 'Withdraw'
    form_class = withdrawForm

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial
    
    def form_valid(self, form):
        account = self.request.user.account
        if account.is_bankrupt == True:
            messages.error(self.request, 'The bank is bankrupt.')
            return self.form_invalid(form)
        else:
            amount = form.cleaned_data.get('amount')
            account.balance -= amount
            account.save(update_fields = ['balance'])
            messages.success(self.request, f'{amount} tk was withdrawn from your account.')
            send_transaction_email('transactions/email_template.html', 'Withdrawal', self.request.user, amount, 'Withdrawal Success Message')
        return super().form_valid(form)
    
class LoanRequestView(TransactionCreateMixin):
    title = 'Request For Loan'
    form_class = LoanRequestForm

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial
    
    def form_valid(self, form):
        account = self.request.user.account
        if account.is_bankrupt == True:
            messages.error(self.request, 'The bank is bankrupt.')
            return self.form_invalid(form)
        else:
            amount = form.cleaned_data.get('amount')
            current_loan__count = Transaction.objects.filter(account = account, loan_approved = True, transaction_type = LOAN).count()

            if current_loan__count >= 3:
                return HttpResponse('you have crossed your loan request limit.')
            
            messages.success(self.request, f'your loan amount {amount} tk is send for approval to the admin')
            send_transaction_email('transactions/email_template.html', 'Loan', self.request.user, amount, 'Loan Request Message')
            return super().form_valid(form)
    
class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account = self.request.user.account
        )

        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            queryset = queryset.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date)

            # self.balance = Transaction.objects.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date).aaggregate(Sum('amount'))['amount__sum']

            self.balance = Transaction.objects.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date
            ).aggregate(Sum('amount'))['amount__sum']

        else:
            self.balance = self.request.user.account.balance
        return queryset.distinct()
    
    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })
        return context
    
class PayLoanView(View):
    def get(self,request,loan_id):
        loan = get_object_or_404(Transaction, id = loan_id)

        if loan.loan_approved:
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.transaction_type = LOAN_PAID
                loan.save()
                messages.success(request, 'you successfully pay your loan.')
                return redirect('loan_list')
            else:
                messages.error(request, 'you have not enough balance to pay loan.')
                return redirect('loan_list')

class LoanListView(LoginRequiredMixin, ListView):
    template_name = 'transactions/loan_request.html'
    model = Transaction
    context_object_name = 'loans'

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account = user_account, transaction_type = LOAN)
        return queryset

####### Money Transfer functionality ######## 
class TransferMoneyView(FormView):
    template_name = 'transactions/transaction_form.html'
    form_class = TransferMoneyForm
    model = Transaction
    success_url = reverse_lazy('transaction_report')

    def form_valid(self, form):
        sender_account = self.request.user.account
        if sender_account.is_bankrupt == True:
            messages.error(self.request, 'The bank is bankrupt.')
            return self.form_invalid(form)
        else:
            receiver_account_no = form.cleaned_data.get('account_no')
            amount = form.cleaned_data.get('amount')
            # Find receiver account that account no user given in the field 
            receiver_account = UserBankAccount.objects.filter(account_no=receiver_account_no).first()
            if receiver_account is not None:
                if sender_account.balance >= amount:
                    sender_account.balance -= amount
                    sender_account.save()
                    Transaction.objects.create(
                        account = sender_account,
                        amount = amount,
                        balance_after_transaction = sender_account.balance,
                        transaction_type = SEND_MONEY,
                        timestamp = datetime.now(),
                        loan_approved = False,
                    )
                    # send user a email for send money
                    send_transaction_email('transactions/email_template.html', 'send money', self.request.user, amount, 'Send Money')
                    

                    receiver_account.balance += amount
                    receiver_account.save()

                    # send user a email for receive money
                    send_transaction_email('transactions/email_template.html', 'receive money', receiver_account.user, amount, 'Received Money')

                    Transaction.objects.create(
                        account = receiver_account,
                        amount = amount,
                        balance_after_transaction = receiver_account.balance,
                        transaction_type = RECEIVED_MONEY,
                        timestamp = datetime.now(),
                        loan_approved = False,
                    )
                    
                    messages.success(self.request, f'your transfer amount {amount} is successfully send.')
                else:
                    messages.error(self.request, 'you have not enough money to send.')        
                return super().form_valid(form)
            else:
                messages.error(self.request, 'User not found!')
                return self.form_invalid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Transfer Money"
        return context
####### Money Transfer functionality ########