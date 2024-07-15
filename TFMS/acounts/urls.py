from django.urls import path
from .views import authentication,farmer, buyer
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='custom_password_reset.html'),
         name='password_reset'),
    path('password_reset_sent/',
         auth_views.PasswordResetDoneView.as_view(template_name='custom_password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='custom_password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password_reset_complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='custom_password_reset_complete.html'),
         name='password_reset_complete'),

    path('index/', authentication.index),
    path('', authentication.user_login, name='login'),
    path('registration/', authentication.registration, name='registration'),
    path('logout/', authentication.user_logout, name='logout'),
    path('change_password/',authentication.change_password, name='change_password'),
    path('update_profile/', authentication.update_profile, name='update_profile'),

    path('buyer/send-notification/', buyer.send_notification, name='send_notification'),
    path('farmer/notifications/', farmer.farmer_notifications, name='farmer_notifications'),



    path('farmerdashboard/', farmer.FarmerDashboard, name='farmer_dashboard'),
    path('loan/', farmer.apply_loan, name='apply_loan'),
    path('edit-product/<int:product_id>/', farmer.edit_product, name='edit_product'),
    path('message/', farmer.send_message, name='send_messages'),
    path('inbox/', farmer.inbox, name='inbox'),

    path('browse_products/', buyer.browse_products, name='browse_products'),
    path('buy_product/<int:product_id>/', buyer.buy_product, name='buy_product'),
    path('view_purchased_products/', buyer.view_purchased_products, name='view_purchased_products'),

    path('buyerdashboard/', buyer.BuyerDashboard, name='buyer_dashboard'),
    path('view_message_conversation/', buyer.view_message_conversation, name='view_message_conversation'),
    path('reply_and_delete_message/', buyer.reply_and_delete_message, name='reply_and_delete_message'),

    path('farmer_loan_request/', buyer.farmer_loan_request, name='farmer_loan_request'),
    path('sold_products/', farmer.view_sold_products, name='view_sold_products'),
    path('view_loan_requests/', farmer.view_loans_requests, name='view_loans_request'),


    path('updates/', authentication.FarmerDetails, name='farmer_details'),
    path('upload_product/', farmer.register_product, name='register_product'),
    path('view_product/', farmer.display_products, name='display_products'),
    path('loan_feedbacks/pdf/', buyer.loan_feedbacks_pdf, name='loan_feedbacks_pdf'),
    path('generate_purchased_products_pdf/', buyer.generate_purchased_products_pdf, name='generate_purchased_products_pdf'),



    # path('display_balances/', farmer.display_balances, name='display_balances'),
    path('reply_message/<str:message_id>/', buyer.reply_message, name='reply_message'),
    path('all_loan_feedback/', buyer.view_all_loan_feedback, name='all_loan_feedback'),

    # path('cancel_sell/<int:order_id>/', farmer.cancel_sell, name='cancel_sell'),

    path('transaction_feedback/<int:loan_request_id>/', buyer.make_transaction, name='transaction_feedback'),
    path('change_password/', authentication.change_password, name='change_password'),

]
