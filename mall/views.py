from django.shortcuts import render
from django.views.generic import ListView

from mall.models import Product


# Create your views here.
def product_list(request):
    qs = Product.objects.select_related("category")
    return render(request, "mall/product_list.html", {"product_list": qs})


class ProductListView(ListView):
    model = Product
    queryset = Product.objects.select_related("category")
    paginate_by = 12


product_list = ProductListView.as_view()
