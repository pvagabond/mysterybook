import random
import string
#import geoip2

import paypalrestsdk
import stripe
# from django.contrib.gis.geoip2 import GeoIP2
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .forms import ReviewForm
from .models import Book, BookOrder, Cart, Review, OrderLineItem


def index(request):
    return render(request, 'template.html')


def store(request):
    books = Book.objects.all()
    context = {
        'books': books,
    }
    return render(request, 'base.html', context)


def book_details(request, book_id):
    book = Book.objects.get(pk=book_id)
    context = {
        'book': Book.objects.get(pk=book_id),
    }
    # try:
    #     geo_info = GeoIP2().city(request.META.get('REMOTE_ADDR'))
    # except geoip2.errors.AddressNotFoundError:
    #     geo_info = GeoIP2().city("97.113.28.248")

    if request.user.is_authenticated:
        if request.method == "POST":
            form = ReviewForm(request.POST)
            if form.is_valid():
                new_review = Review.objects.create(
                    user=request.user,
                    book=context['book'],
                    text=form.cleaned_data.get('text'),
                    latitude= 12, #geo_info['latitude'],
                    longitude= 100 #geo_info['longitude']
                )
                new_review.save()
                if Review.objects.filter(user=request.user, book=context['book']).count() < 6:
                    subject = "Your MysteryBook.com discount is here:"
                    from_email = 'library@myesterybooks.com'
                    to_mail = [request.user.email]

                    email_context = {
                        'username': request.user.username,
                        'code': ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6)),
                        'discount': 10
                    }

                    text_email = render_to_string('email/review_email.txt', email_context)
                    html_email = render_to_string('email/review_email.html', email_context)

                    msg = EmailMultiAlternatives(subject, text_email, from_email, to_mail)
                    msg.attach_alternative(html_email, 'text/html')
                    msg.content_subtype = 'html'
                    msg.send()
        else:
            if Review.objects.filter(user=request.user, book=context['book']).count() == 0:
                form = ReviewForm()
                context['form'] = form

    context['geo_info'] = {'latitude': 39.9042, 'longitude': 116.4074} #geo_info

    context['reviews'] = book.review_set.all()
    return render(request, 'store/detail.html', context)


def add_to_cart(request, book_id):
    if request.user.is_authenticated:
        try:
            Book.objects.get(pk=book_id)
        except ObjectDoesNotExist:
            pass
        else:
            try:
                my_cart = Cart.objects.get(user=request.user, active=True)
            except ObjectDoesNotExist:
                my_cart = Cart.objects.create(user=request.user)
                my_cart.save()
            my_cart.add_to_cart(book_id)
        return redirect('cart')
    else:
        return redirect('index')


def remove_from_cart(request, book_id):
    if request.user.is_authenticated:
        try:
            book = Book.objects.get(pk=book_id)
        except ObjectDoesNotExist:
            pass
        else:
            cart = Cart.objects.get(user=request.user, active=True)
            cart.remove_from_cart(book_id)
        return redirect('cart')
    else:
        return redirect('index')


def cart(request):
    if request.user.is_authenticated:
        my_cart = Cart.objects.filter(user=request.user, active=True)
        orders = BookOrder.objects.filter(cart=my_cart[0]) if my_cart else []
        lineItems = OrderLineItem.objects.filter(order=orders[0]) if orders else []
        total = 0
        count = 0
        for lineItem in lineItems:
            total += (lineItem.book.price * lineItem.quantity)
            count += lineItem.quantity
        context = {
            'cart': lineItems,
            'total': total,
            'count': count,
        }
        return render(request, 'store/cart.html', context)

    else:
        return redirect('index')


def checkout(req, processor):
    if req.user.is_authenticated:
        cart = Cart.objects.filter(user=req.user.id, active=True)
        orders = BookOrder.objects.filter(cart=cart[0])
        lineItems = OrderLineItem.objects.filter(order=orders[0])

        if processor == "paypal":
            redirect_url = checkout_paypal(req, cart, lineItems)
            return redirect(redirect_url)
        elif processor == "stripe":
            token = req.POST['stripeToken']
            status = checkout_stripe(cart, lineItems, token)

            if status:
                return redirect(reverse('process_order', args=['stripe']))
            else:
                return redirect('order_error', context={"message": "There was a problem processing your payment."})
        else:
            return redirect('index')


def checkout_paypal(req, cart, orders):
    if req.user.is_authenticated:
        items = []
        total = 0
        for order in orders:
            total += (order.book.price * order.quantity)
            book = order.book
            item = {
                'name': book.title,
                'sku': book.id,
                'price': str(book.price),
                'currency': 'USD',
                'quantity': order.quantity
            }
            items.append(item)

        paypalrestsdk.configure({
            "mode": "sandbox",
            "client_id": "Abn2psKnCVmo3sHOVE57ObmjFtlQzwe8_Qj0bj2CWfIX_g6itJNZiHqdZ5hw3hAdIZeTvXOOFEN5eJm6",
            "client_secret": "EDxrUJV6t3vUrw8xTXaqTGsTyq8oDCaeFiWneeD8m0DlJICCv1Rn57k9dPZ6O0n2jKDKKTI-lTOjiidt"
        })

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": "http://localhost:8000/store/process/paypal",
                "cancel_url": "http://localhost:8000/store"
            },
            "transactions": [
                {
                    "item_list": {
                        "items": items
                    },
                    "amount": {
                        "total": str(total),
                        "currency": "USD"
                    },
                    "description": "Mystery Book order"
                }
            ]
        })

        if payment.create():
            cart_instance = cart.get()
            cart_instance.payment_id = payment.id
            cart_instance.save()
            for link in payment.links:
                if link.method == "REDIRECT":
                    redirect_url = str(link.href)
                    return redirect_url
        else:
            return reverse('order_error')
    else:
        return redirect('index')


def checkout_stripe(my_cart, orders, token):
    stripe.api_key = "sk_test_6RZARYd2C2HJWuvk7jHg0uCB"
    total = 0
    for order in orders:
        total += (order.book.price * order.quantity)
    status = True
    try:
        charge = stripe.Charge.create(
            amount=int(total * 100),
            currency="USD",
            source=token,
            metadata={'order_id': my_cart.get().id}
        )
        cart_instance = my_cart.get()
        cart_instance.payment_id = charge.id
        cart_instance.save()
    except stripe.error.CardError:
        status = False
    return status


def order_error(req):
    if req.user.is_authenticated:
        return render(req, 'store/order_error.html')
    else:
        return redirect('index')


def process_order(req, processor):
    if req.user.is_authenticated:
        if processor == 'paypal':
            payment_id = req.GET.get('paymentId')
            my_cart = Cart.objects.filter(payment_id=payment_id)
            orders = BookOrder.objects.filter(cart=my_cart[0])
            total = 0
            for order in orders:
                total += (order.book.price * order.quantity)
            context = {
                'cart': orders,
                'total': total
            }
            return render(req, 'store/process_order.html', context)
        elif processor == 'stripe':
            return JsonResponse({'redirect_url': reverse('complete_order', args=['stripe'])})
    else:
        return redirect('index')


def complete_order(req, processor):
    if req.user.is_authenticated:
        my_cart = Cart.objects.get(user=req.user.id, active=True)
        my_cart.payment_type = processor
        if processor == 'paypal':
            payment = paypalrestsdk.Payment.find(my_cart.payment_id)
            if payment.execute({
                "payer_id": payment.payer.payer_info.payer_id
            }):
                message = "Success: Your order has been complete, and the payment ID is %s" % (payment.id)
                my_cart.active = False
                my_cart.order_date = timezone.now()
                my_cart.save()
            else:
                message = "There was a problem with the transaction. Error: %s" % (payment.error.message)
            context = {
                "message": message
            }
            return render(req, 'store/order_complete.html', context)
        elif processor == 'stripe':
            my_cart.active = False
            my_cart.order_date = timezone.now()
            my_cart.save()
            message = "Success: Your order has been complete, and the payment ID is %s" % (my_cart.payment_id)
            context = {
                'message': message
            }
            return render(req, 'store/order_complete.html', context)
    else:
        return redirect('index')

def order(request):
    if request.user.is_authenticated:
        my_carts = Cart.objects.filter(user=request.user, active=False)
        orders = []
        for cart in my_carts:
            order = dict()
            bookOrders = BookOrder.objects.filter(cart=cart)
            lineItems = OrderLineItem.objects.filter(order=bookOrders[0]) if bookOrders else []
            total = 0
            count = 0
            for lineItem in lineItems:
                total += (lineItem.book.price * lineItem.quantity)
                count += lineItem.quantity
            order['total'] = total
            order['count'] = count
            order['lineItems'] = lineItems
            order['orderDate'] = cart.order_date
            order['Id'] = bookOrders[0].orderId
            orders.append(order)
        context = {
            'orders': orders,
        }
        return render(request, 'store/order.html', context)

    else:
        return redirect('index')


