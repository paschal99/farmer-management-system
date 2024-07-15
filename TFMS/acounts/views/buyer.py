from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from ..sms import *
import datetime
from django.db.models import F
import logging
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from ..forms import *
from django.http import JsonResponse


def loan_feedbacks_pdf(request):
    loan_feedbacks = LoanFeedback.objects.all()  # Retrieve all LoanFeedback instances
    current_year = datetime.datetime.now().year
    html_string = render_to_string('buyer/loan_pdf.html',
                                   {'loan_feedbacks': loan_feedbacks, 'current_year': current_year})

    # Create a PDF from the HTML string
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="loan_feedbacks.pdf"'

    # Generate PDF
    pisa_status = pisa.CreatePDF(html_string, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
    return response

@login_required(login_url='/login/')
def BuyerDashboard(request):
    feedbacks = LoanFeedback.objects.all()
    total_loan_amount = LoanFeedback.objects.aggregate(total_loan=models.Sum('amount_transferred'))['total_loan']
    account, created = Account.objects.get_or_create(user=request.user)
    return render(request, 'buyer/buyerdashboard.html',{'balance': account.balance, 'feedbacks': feedbacks, 'total_loan_amount': total_loan_amount})
@login_required(login_url='/login/')
def reply_message(request, message_id):
    maseji = Message.objects.all()
    message = Message.objects.get(pk=message_id)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            sender = request.user
            receiver = message.sender
            feedback = Feedback.objects.create(sender=sender, receiver=receiver, content=content)
            return redirect('inbox')
    else:
        form = FeedbackForm()
    return render(request, 'buyer/view_conversation.html', {'form': form, 'message': message})



@login_required(login_url='/login/')
def farmer_loan_request(request):
    if request.method == 'GET' and request.GET.get('user_id'):
        user_id = request.GET.get('user_id')
        user = get_object_or_404(User, id=user_id)
        loan_requestor = get_object_or_404(LoanRequest, user=user)

        # You may want to fetch additional details from the user or loan requestor here

        return JsonResponse({'username': user.username, 'phone': user.profile.phone, 'location': user.profile.location, 'amount_requested': loan_requestor.amount_requested, 'reason': loan_requestor.reason})

    else:
        # Retrieve all pending loan requests
        loan_requestor = LoanRequest.objects.filter(status='Pending')
        return render(request, 'buyer/loan_requestor.html', {'loan_requestor': loan_requestor})

@login_required(login_url='/login/')
def make_transaction(request, loan_request_id):
    loan_request = get_object_or_404(LoanRequest, pk=loan_request_id)
    message = None

    if request.method == 'POST':
        try:
            # Retrieve buyer's account
            buyer_account = Account.objects.get(user=request.user)

            # Check if the buyer has sufficient balance
            if buyer_account.balance < loan_request.amount_requested:
                message = 'Insufficient balance.'
            else:
                # Retrieve loan requestor's account
                requestor_account = loan_request.account

                # Perform the transaction within a transaction block to ensure data consistency
                with transaction.atomic():
                    # Deduct the requested amount from the buyer's account
                    buyer_account.balance -= loan_request.amount_requested
                    buyer_account.save()

                    # Add the requested amount to the loan requestor's account
                    requestor_account.balance += loan_request.amount_requested
                    requestor_account.save()

                    # Update the loan request status to 'Approved'
                    loan_request.status = 'Approved'
                    loan_request.loan_amount = loan_request.amount_requested  # Update the loan amount
                    loan_request.save()

                    # Create a feedback object for the transaction
                    LoanFeedback.objects.create(
                        loan_request=loan_request,
                        from_account=buyer_account,
                        to_account=requestor_account,
                        amount_transferred=loan_request.amount_requested,
                    )

                    message = 'Transaction successful.'

                    profile = Profile.objects.get(user=loan_request.user)
                    phone_number = '255' + profile.phone.lstrip('0')
                    message = f"Dear {loan_request.user.username}, your loan request for {loan_request.amount_requested} has been approved."
                    send_sms(phone_number, message)

                    # # Retrieve or create the loan requestor's profile to get phone number and username
                    # requestor_profile, created = Profile.objects.get_or_create(user=requestor_account.user)
                    #
                    # # Send SMS notification via Beem Africa
                    # send_sms([requestor_profile.phone], f"Dear {requestor_account.user.username}, your loan request of {loan_request.amount_requested} has been approved and credited to your account.")

        except LoanRequest.DoesNotExist:
            message = 'Loan request not found.'
        except Account.DoesNotExist:
            message = 'Account not found.'
        except Profile.DoesNotExist:
            message = 'Profile not found.'
        except Exception as e:
            message = str(e)

    return render(request, 'buyer/make_transaction.html', {
        'loan_request': loan_request,
        'message': message,
    })


def browse_products(request):
    all_products = Product.objects.filter( payment_status='Pending')
    paginator = Paginator(all_products, 6)  # Show 6 products per page

    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        products = paginator.page(paginator.num_pages)

    return render(request, 'buyer/browse_products.html', {'products': products})


def view_all_loan_feedback(request):
    # Fetch all loan feedback made by buyers
    feedbacks = LoanFeedback.objects.all()
    return render(request, 'buyer/all_loan_feedback.html', {'feedbacks': feedbacks})


logger = logging.getLogger(__name__)
@login_required
def buy_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    total_amount = product.total_price() * product.quantity_available

    if request.method == 'POST':
        try:
            with transaction.atomic():
                buyer_account = Account.objects.select_for_update().get(user=request.user)
                seller_account = Account.objects.select_for_update().get(user=product.seller)

                if buyer_account.balance >= total_amount:
                    # Check if seller has a pending loan
                    pending_loan_feedback = LoanFeedback.objects.filter(loan_request__user=product.seller, loan_request__status='Pending').first()

                    if pending_loan_feedback:
                        # Deduct loan amount from seller's account and add it to buyer's account
                        loan_amount = pending_loan_feedback.loan_request.amount_requested
                        seller_account.balance = F('balance') - loan_amount
                        seller_account.save()

                        buyer_account.balance = F('balance') + loan_amount
                        buyer_account.save()

                        # Update loan request status
                        pending_loan_feedback.loan_request.status = 'Approved'
                        pending_loan_feedback.loan_request.save()

                        # Update loan feedback status
                        pending_loan_feedback.status = 'Completed'
                        pending_loan_feedback.save()

                    # Deduct amount from buyer's account
                    buyer_account.balance -= total_amount
                    buyer_account.save()

                    # Add amount to seller's account
                    seller_account.balance += total_amount
                    seller_account.save()

                    # Create order
                    Order.objects.create(
                        buyer=request.user,
                        product=product,
                        quantity_ordered=product.quantity_available,
                        total_amount=total_amount
                    )

                    # Update product status
                    product.quantity_available = 0
                    product.payment_status = 'sold_out'
                    product.save()

                    messages.success(request, 'Purchase successful!')
                    return redirect('buyer_dashboard')  # Adjust the URL name accordingly
                else:
                    messages.error(request, 'Insufficient balance to complete the purchase.')

        except Account.DoesNotExist as e:
            messages.error(request, f"Account error: {e}")
        except Exception as e:
            messages.error(request, f"Unexpected error: {e}")

    return render(request, 'buyer/buy_product.html', {'product': product, 'total_amount': total_amount})

def view_purchased_products(request):
    # Assuming the user is authenticated and you have a way to identify the buyer
    buyer = request.user  # Change this to your actual buyer identification method

    # Fetch all orders made by the current buyer
    orders = Order.objects.filter(buyer=buyer)

    # Paginate the orders
    paginator = Paginator(orders, 5)  # Show 10 orders per page

    page = request.GET.get('page')
    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        orders_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        orders_page = paginator.page(paginator.num_pages)

    return render(request, 'buyer/purchased_products.html', {'orders_page': orders_page})


def view_message_conversation(request, message_id=None):
    if request.method == 'POST':
        if 'delete_message' in request.POST:
            message_id = request.POST.get('message_id')
            message = get_object_or_404(Message, id=message_id)
            message.delete()
            return redirect('view_message_conversation')

        elif 'replyContent' in request.POST:
            content = request.POST.get('replyContent')
            receiver_username = request.POST.get('receiver')
            receiver = get_object_or_404(User, username=receiver_username)
            feedback = Feedback(sender=request.user, receiver=receiver, content=content)
            feedback.save()
            return redirect('view_message_conversation')

    received_messages = Message.objects.filter(receiver=request.user)
    sent_messages = Message.objects.filter(sender=request.user)
    return render(request, 'buyer/view_conversation.html', {'received_messages': received_messages, 'sent_messages': sent_messages})


def reply_and_delete_message(request):
    if request.method == 'POST':
        # Check if reply form is submitted
        if 'replyContent' in request.POST:
            receiver_username = request.POST.get('receiver')
            content = request.POST.get('replyContent')
            if receiver_username and content:
                receiver = get_object_or_404(User, username=receiver_username)
                new_message = Message(sender=request.user, receiver=receiver, content=content)
                new_message.save()
                messages.success(request, 'Message sent successfully.')

        # Check if delete form is submitted
        elif 'message_id' in request.POST:
            message_id = request.POST.get('message_id')
            if message_id:
                message = get_object_or_404(Message, id=message_id)
                message.delete()
                messages.success(request, 'Message deleted successfully.')

        return redirect('view_message_conversation')

    return render(request, 'buyer/view_conversation.html')  # Replace with your template
def generate_purchased_products_pdf(request):
    # Assuming the user is authenticated and you have a way to identify the buyer
    buyer = request.user  # Change this to your actual buyer identification method

    # Fetch all orders made by the current buyer
    orders = Order.objects.filter(buyer=buyer)

    # Render HTML template with all orders
    html_string = render_to_string('buyer/purchased_goods_pdf.html', {'orders': orders})

    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="purchased_goods_pdf.pdf"'

    # Generate PDF
    pisa_status = pisa.CreatePDF(html_string, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
    return response

def send_notification(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        if title and content:
            sender = request.user
            Notification.objects.create(sender=sender, title=title, content=content)
            return redirect('buyer_dashboard')  # Redirect to buyer dashboard after sending
        else:
            # Handle invalid form submission
            return render(request, 'buyer/send_notification.html', {'error': 'Please fill in all fields.'})
    return render(request, 'buyer/send_notification.html')