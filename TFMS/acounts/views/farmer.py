from django.http import HttpResponseForbidden, HttpResponse
from django.contrib import messages
from ..models import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from ..forms import *
from django.contrib.auth.decorators import login_required



@login_required(login_url='/login/')
def apply_loan(request):
    user = request.user
    try:
        account = Account.objects.filter(user=user).first()
    except Account.DoesNotExist:
        # If the account doesn't exist, create a new one
        account = Account.objects.create(user=user)
        # Optionally, set the initial balance for the account
        account.balance = 0
        account.save()

    if request.method == 'POST':
        form = LoanRequestForm(request.POST)
        if form.is_valid():
            loan_request = form.save(commit=False)
            loan_request.user = user
            loan_request.account = account
            loan_request.save()
            return redirect('apply_loan')  # Redirect back to the same page to display loan applications
    else:
        form = LoanRequestForm()
    return render(request, 'farmer/farmerloan.html', {'form':form})


def view_loans_requests(request):
    user = request.user

    # Handle loan cancellation
    if request.method == 'POST' and 'loan_request_id' in request.POST:
        loan_request_id = request.POST.get('loan_request_id')
        loan_request = LoanRequest.objects.filter(id=loan_request_id, user=user).first()

        if not loan_request:
            messages.error(request, "You are not authorized to cancel this loan application or it does not exist.")
            return redirect('loan_requests_view')

        loan_request.delete()
        messages.success(request, 'Loan request has been successfully canceled.')
        return redirect('view_loans_request')

    # Fetch user's loan applications
    loan_applications = LoanRequest.objects.filter(user=user)
    return render(request, 'farmer/loandetails.html', {'loan_applications': loan_applications})


def send_message(request):
    # Get the default buyer
    default_buyer = User.objects.filter(profile__role='buyer').first()

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            sender = request.user
            receiver = default_buyer
            Message.objects.create(sender=sender, receiver=receiver, content=content)
            # Redirect back to the messages page after sending the message
            return redirect('send_messages')
        else:
            return HttpResponse('Invalid request')  # Handle invalid requests
    else:
        # Retrieve both sent and received messages for the logged-in user
        received_messages = Message.objects.filter(receiver=request.user)
        sent_messages = Message.objects.filter(sender=request.user)
        received_feedback = Feedback.objects.filter(receiver=request.user)
        sent_feedback = Feedback.objects.filter(sender=request.user)

        context = {
            'received_messages': received_messages,
            'sent_messages': sent_messages,
            'received_feedback': received_feedback,
            'sent_feedback': sent_feedback,
        }

        return render(request, 'farmer/received_message.html', context)


@login_required(login_url='/login/')
def inbox(request):
    if request.user.profile.role == 'farmer':
        # Mnunuzi: Anapokea ujumbe kutoka kwa wakulima na anaweza kutuma majibu
        received_messages = Feedback.objects.filter(receiver=request.user)
        sent_messages = Message.objects.filter(sender=request.user)
    elif request.user.profile.role == 'farmer':

        received_messages = Feedback.objects.filter(receiver=request.user)
        sent_messages = Message.objects.filter(sender=request.user)
    else:
        received_messages = []
        sent_messages = []

    return render(request, 'farmer/received_message.html',
                  {'received_messages': received_messages, 'sent_messages': sent_messages})


def view_sold_products(request):
    # Get all orders where the current user (seller) is the buyer
    farmer = request.user
    sold_orders = Order.objects.filter(buyer=farmer)
    return render(request, 'farmer/sell_product.html', {'sold_orders': sold_orders})


@login_required(login_url='/login/')
def FarmerDashboard(request):
    account, created = Account.objects.get_or_create(user=request.user)
    notifications = Notification.objects.all().order_by('-date_sent')

    return render(request, 'farmer/farmerdashboard.html', {'balance': account.balance, 'notifications': notifications})



@login_required
def register_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        quantity_available = request.POST.get('quantity_available')
        price_per_unit = request.POST.get('price_per_unit')
        image = request.FILES.get('image')
        seller = request.user

        product = Product.objects.create(
            name=name,
            description=description,
            quantity_available=quantity_available,
            price_per_unit=price_per_unit,
            image=image,
            seller=seller
        )
        return redirect('farmer_dashboard')  # Change 'dashboard' to the appropriate URL name

    return render(request, 'farmer/product_registration.html')


@login_required(login_url='/login/')
def display_products(request):
    if request.method == 'POST':
        # Handle product deletion
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id, seller=request.user)
        product.delete()
        messages.success(request, 'Product successfully deleted.')
        return redirect('display_products')

    # Retrieve products associated with the currently logged-in user
    products = Product.objects.filter(seller=request.user)

    # Pagination
    page_number = request.GET.get('page')
    paginator = Paginator(products, 10)  # 10 products per page
    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        products = paginator.page(paginator.num_pages)

    return render(request, 'farmer/product_display.html', {'products': products})


def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        # Retrieve the updated data from the request
        name = request.POST.get('name')
        delivered = request.POST.get('delivered')
        quantity_available = request.POST.get('quantity_available')
        price_per_unit = request.POST.get('price_per_unit')

        # Update the product object
        product.name = name
        product.delivered =  delivered
        product.quantity_available = quantity_available
        product.price_per_unit = price_per_unit
        product.save()

        return redirect('display_products')
    return render(request, 'farmer/edit_product.html', {'product': product})


def farmer_notifications(request):
    notifications = Notification.objects.all().order_by('-date_sent')
    context = {
        'notifications': notifications,
    }
    return render(request, 'farmer/view_notifications.html', context)