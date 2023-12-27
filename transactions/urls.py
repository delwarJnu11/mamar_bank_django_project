from django.urls import path
from transactions.views import DepositMoneyView, WithdrawMoneyView, LoanRequestView, PayLoanView, LoanListView, TransactionReportView

urlpatterns = [
    path('deposit/', DepositMoneyView.as_view(), name='deposit'),
    path('withdraw/', WithdrawMoneyView.as_view(), name='withdraw'),
    path('loan_request/', LoanRequestView.as_view(), name='loan_request'),
    path('report/', TransactionReportView.as_view(), name='transaction_report'),
    path('loans/', LoanListView.as_view(), name='loan_list'),
    path('loan/<int:loan_id>/', PayLoanView.as_view(), name='pay_loan'),
]
