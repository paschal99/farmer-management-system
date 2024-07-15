from django.contrib import admin
from .models import *


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_requested', 'amount_requested', 'status', 'reason', 'loan_amount', 'account')
    search_fields = ['user__username', 'status']


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('balance', 'user')
    search_fields = ['user__username']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content', 'date_sent')
    search_fields = ['sender__username', 'receiver__username']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content', 'date_sent')
    search_fields = ['sender__username', 'receiver__username']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('seller', 'name', 'quantity_available', 'price_per_unit')
    search_fields = ['seller__username', 'name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'product', 'quantity_ordered', 'total_amount', 'order_date',)
    search_fields = ['buyer__username', 'product__name', 'payment_status']



class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'location', 'sex', 'role')
    search_fields = ('user__username', 'phone', 'location')
    list_filter = ('sex', 'role')

admin.site.register(Profile, ProfileAdmin)
