from django import forms
from mall.models import CartProduct


class CartProductForm(forms.ModelForm):
    class Meta:
        model = CartProduct
        fields = ["quantity"]
