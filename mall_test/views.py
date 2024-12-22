from django.shortcuts import render


# Create your views here.
def payment_new(request):
    return render(request, "mall_test/payment_form.html")
