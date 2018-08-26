from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from random import seed, random


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __str__(self):
        return "%s, %s" % (self.last_name, self.first_name)


def cover_upload_path(instance, filename):
    return '/'.join(['books', str(instance.id), filename])


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    description = models.TextField()
    publish_date = models.DateField(default=timezone.now)
    price = models.DecimalField(decimal_places=2, max_digits=8)
    stock = models.IntegerField(default=0)
    cover_image = models.ImageField(upload_to=cover_upload_path, default='books/empty_cover.jpg')


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    publish_date = models.DateField(default=timezone.now)
    text = models.TextField()
    latitude = models.FloatField(max_length=20, default="37.419")
    longitude = models.FloatField(max_length=20, default="122.05")


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    order_date = models.DateField(null=True)
    payment_type = models.CharField(max_length=100, null=True)
    payment_id = models.CharField(max_length=100, null=True)

    def add_to_cart(self, book_id):
        book = Book.objects.get(pk=book_id)
        try:
            prexisting_order = BookOrder.objects.get(cart=self)
            prexisting_order.add_to_line_itme(book=book)
        except BookOrder.DoesNotExist:
            new_order = BookOrder.objects.create(cart=self)
            new_lineItem = OrderLineItem.objects.create(book=book, order=new_order, quantity=1)

    def remove_from_cart(self, book_id):
        book = Book.objects.get(pk=book_id)
        try:
            prexisting_order = BookOrder.objects.get(cart=self)
            prexisting_lineItem = OrderLineItem.objects.get(order=prexisting_order, book=book)
            if prexisting_lineItem.quantity > 1:
                prexisting_lineItem.quantity -= 1
                prexisting_lineItem.save()
            else:
                prexisting_lineItem.delete()
        except BookOrder.DoesNotExist:
            pass


class BookOrder(models.Model):
    seed(1)
    orderId = models.IntegerField(default=random()*10)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)

    def add_to_line_itme(self, book):
        try:
            prexisting_lineItem = OrderLineItem.objects.get(book=book, order=self)
            prexisting_lineItem.quantity +=1
            prexisting_lineItem.save()
        except OrderLineItem.DoesNotExist:
            new_lineItem = OrderLineItem.objects.create(book=book, order=self, quantity=1)


class OrderLineItem(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    order = models.ForeignKey(BookOrder, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
