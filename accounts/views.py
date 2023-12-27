from django.shortcuts import render,redirect
from django.urls import reverse_lazy
from django.contrib.auth import login, logout
from django.views.generic import FormView,View
from accounts.forms import UserRegistrationForm
from django.contrib.auth.views import LoginView
from accounts.forms import UserUpdateForm

# Create your views here.
class UserRegistrationView(FormView):
    form_class = UserRegistrationForm
    template_name = 'accounts/user_registration.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)
    
# User Login View
class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'

    def get_success_url(self):
        return reverse_lazy('home')
    
class UserLogoutView(View):
    
    def get(self,request):
        if request.user.is_authenticated:
            logout(request)
            return redirect('home')
        
class UserBankAccountUpdateView(View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        form = UserUpdateForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the user's profile page
        return render(request, self.template_name, {'form': form})
    

    
