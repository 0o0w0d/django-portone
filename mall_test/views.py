from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from mall_test.models import Payment
from mall_test.forms import PaymentForm


# Create your views here.
def payment_new(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            return redirect("payment_pay", pk=payment.pk)
    else:
        form = PaymentForm()
    return render(request, "mall_test/payment_form.html", {"form": form})


def payment_pay(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    payment_props = {
        "pg": settings.PORTONE_PG,
        "merchant_uid": payment.merchant_uid,
        "name": payment.name,
        "amount": payment.amount,
    }
    payment_check_url = reverse("payment_check", args=[payment.pk])
    portone_shop_id = settings.PORTONE_SHOP_ID

    return render(
        request,
        "mall_test/payment_pay.html",
        {
            "payment_props": payment_props,
            "payment_check_url": payment_check_url,
            "portone_shop_id": portone_shop_id,
        },
    )


def payment_check(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    payment.portone_check()
    return redirect("payment_detail", pk=payment.pk)


def payment_detail(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, "mall_test/payment_detail.html", {"payment": payment})
