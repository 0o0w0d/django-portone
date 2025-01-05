from django.forms import modelformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages

from django.conf import settings
from mall.forms import CartProductForm
from mall.models import CartProduct, Order, OrderPayment, Product


# Create your views here.
def product_list(request):
    qs = Product.objects.filter(status=Product.Status.ACTIVE).select_related("category")
    return render(request, "mall/product_list.html", {"product_list": qs})


class ProductListView(ListView):
    model = Product
    queryset = Product.objects.filter(status=Product.Status.ACTIVE).select_related(
        "category"
    )
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get("query", "")
        if query:
            qs = qs.filter(name__icontains=query)
        return qs


product_list = ProductListView.as_view()


@login_required
def cart_detail(request):
    user = request.user
    cart_qs = (
        CartProduct.objects.filter(user=user)
        .select_related("product")
        .order_by("product__name")
    )

    CartProductFormSet = modelformset_factory(
        model=CartProduct, form=CartProductForm, can_delete=True, extra=0
    )

    if request.method == "POST":
        formset = CartProductFormSet(data=request.POST, queryset=cart_qs)
        if formset.is_valid():
            formset.save()
            messages.success(request, "장바구니를 업데이트했습니다.")
            return redirect("cart_detail")
    else:
        formset = CartProductFormSet(queryset=cart_qs)

    return render(request, "mall/cart_detail.html", {"formset": formset})


@login_required
@require_POST
def add_to_cart(request, product_pk):
    user = request.user
    product_qs = Product.objects.filter(status=Product.Status.ACTIVE)
    product = get_object_or_404(product_qs, pk=product_pk)

    quantity = int(request.GET.get("quantity", 1))

    cart_product, is_created = CartProduct.objects.get_or_create(
        user=user, product=product, defaults={"quantity": quantity}
    )

    if not is_created:
        cart_product.quantity += quantity
        cart_product.save()

    # messages.success(request, "장바구니에 추가했습니다.")

    # redirect_url = request.META.get("HTTP_REFERER", "product_list")
    # return redirect(redirect_url)
    return JsonResponse({"statusCode": 200})


@login_required
def order_new(request):
    user = request.user
    cart_product_qs = CartProduct.objects.filter(user=user)

    # 주문 생성 -> 장바구니 삭제
    order = Order.create_from_cart(user=user, cart_product_ps=cart_product_qs)
    cart_product_qs.delete()

    return redirect("order_pay", order.pk)


@login_required
def order_pay(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    # 결제를 진행해도 되는 상황인지 확인하는 메서드 => 비즈니스 로직은 models.py에 구현현
    if not order.can_pay():
        messages.error(request, "현재 결제를 할 수 없는 주문입니다.")
        return redirect("order_detail", order.pk)  # TODO: order_detail 구현 필요

    # order로부터 payment 생성
    payment = OrderPayment.create_by_order(order)

    payment_props = {
        "pg": settings.PORTONE_PG,
        "merchant_uid": payment.merchant_uid,
        "name": payment.name,
        "amount": payment.desired_amount,
        "buyer_name": payment.buyer_name or request.user.username,
        "buyer_email": payment.buyer_email,
    }

    return render(
        request,
        "mall/order_pay.html",
        {
            "payment_props": payment_props,
            "portone_shop_id": settings.PORTONE_SHOP_ID,
            "next_url": reverse("order_check", args=[order.pk, payment.pk]),
        },
    )


@login_required
def order_check(request, order_pk, payment_pk):
    payment = get_object_or_404(OrderPayment, pk=payment_pk, order__user=request.user)
    # payment.update()
    # return redirect("order_detail", order_pk)  # TODO: order_detail 구현 예정
    return HttpResponse("order check page")
