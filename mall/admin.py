from django.contrib import admin

from mall.models import CartProduct, Category, Order, OrderPayment, Product

# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["pk", "name"]
    list_display_links = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["category", "name", "price", "status"]
    list_display_links = ["name"]
    list_filter = ["category", "status", "created_at", "updated_at"]
    date_hierarchy = "updated_at"
    actions = ["make_active"]

    @admin.display(
        description=f"지정 상품을 {Product.Status.ACTIVE.label} 상태로 변경합니다"
    )
    def make_active(self, request, queryset):
        count = queryset.update(status=Product.Status.ACTIVE)
        # for q in queryset:
        #     q.status = Product.status.ACTIVE
        #     q.save()
        self.message_user(
            request,
            f"{count}개의 상품을 {Product.Status.ACTIVE.label} 상태로 변경했습니다.",
        )


@admin.register(CartProduct)
class CartProductAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    pass
