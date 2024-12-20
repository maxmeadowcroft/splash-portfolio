from django.urls import path
from . import views

urlpatterns = [
    path('', views.signup, name='signup'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('forget_password/', views.forget_password, name='forget_password'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('accounts/', views.accounts, name='accounts'),
    path('logout/', views.user_logout, name='logout'),
    path('portfolio/<str:username>/', views.portfolio, name='portfolio'),
    path('projects/', views.projects, name='projects'),
    path('projects/edit/<int:id>/', views.edit_project, name='edit_project'),  # Edit project view
    path('projects/delete/<int:id>/', views.delete_project, name='delete_project'),
    path('projects/<int:id>/', views.show_project ,name='show_project'),
    path('payment/', views.payment_view, name='payment'),
    path('confirm_payment/', views.confirm_payment, name='confirm_payment'),
    path('premium_subcription/', views.subscribe_to_premium, name='subscribe_to_premium'),
    path('transaction_history/', views.transaction_history, name='transaction_history'),
    path('contact/<str:username>/', views.contact, name='contact'),

]
