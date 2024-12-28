from django.shortcuts import render

from mall.models import Product


# Create your views here.
def product_list(request):
    qs = Product.objects.select_related("category")
    return render(request, "mall/product_list.html", {"product_list": qs})
