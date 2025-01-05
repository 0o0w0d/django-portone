from functools import cached_property
from typing import List
from uuid import uuid4
import logging
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import UniqueConstraint
from django.db.models import QuerySet
from django.http import Http404
from iamport import Iamport

from accounts.models import User
from django.conf import settings


logger = logging.getLogger(__name__)


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = verbose_name_plural = "상품 분류"


class Product(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "a", "정상"
        SOLD_OUT = "s", "품절"
        OBSOLETE = "o", "단종"
        INACTIVE = "i", "비활성화"

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, db_constraint=False
    )
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField()
    status = models.CharField(
        choices=Status.choices, default=Status.INACTIVE, max_length=1
    )
    photo = models.ImageField(upload_to="mall/product/photo/%Y/%m/%d")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.pk}] {self.name}"

    class Meta:
        verbose_name = verbose_name_plural = "상품"
        ordering = ["-pk"]


class CartProduct(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="cart_product_set",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_constraint=False)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    def __str__(self):
        return f"[{self.pk}] {self.product.name} - {self.quantity}개"

    class Meta:
        verbose_name_plural = verbose_name = "장바구니 상품"
        constraints = [
            UniqueConstraint(fields=["user", "product"], name="unique_user_product")
        ]

    @property
    def amount(self):
        return self.product.price * self.quantity


class Order(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "주문 요청"
        FAILED_PAYMEMT = "failed_payment", "결제 실패"
        PAID = "paid", "결제 완료"
        PREPARED_PRODUCT = "prepared_product", "상품 준비중"
        SHIPPED = "shipped", "배송중"
        DELIVERED = "delivered", "배송완료"
        CANCELED = "canceled", "주문 취소"

    uid = models.UUIDField(default=uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_constraint=False
    )
    total_amount = models.PositiveIntegerField(verbose_name="결제 금액")
    status = models.CharField(
        verbose_name="진행 상황",
        choices=Status.choices,
        default=Status.REQUESTED,
        max_length=20,
        db_index=True,
    )
    product_set = models.ManyToManyField(Product, through="OrderedProduct", blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def create_from_cart(
        cls, user: User, cart_product_ps: QuerySet[CartProduct]
    ) -> "Order":
        # 리스트를 생성해 DB 조회가 1번만 실행되도록
        cart_product_list: List[CartProduct] = list(cart_product_ps)
        total_amount = sum(cart_product.amount for cart_product in cart_product_list)
        order = cls.objects.create(user=user, total_amount=total_amount)

        ordered_product_list = []
        for cart_product in cart_product_list:
            ordered_product = OrderedProduct(
                order=order,
                product=cart_product.product,
                name=cart_product.product.name,
                price=cart_product.product.price,
                quantity=cart_product.quantity,
            )
            ordered_product_list.append(ordered_product)

        OrderedProduct.objects.bulk_create(ordered_product_list)
        return order

    @property
    def name(self):
        first_product = self.orderedproduct_set.first()
        if first_product is None:
            return "등록된 상품이 없습니다."
        size = self.orderedproduct_set.all().count()
        if size < 2:
            return first_product.name
        return f"{first_product.name} 외 {size - 1}건"

    def can_pay(self) -> bool:
        return self.status in (self.Status.REQUESTED, self.Status.FAILED_PAYMEMT)


# order - product M2M으로 연결하는 모델
class OrderedProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_constraint=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_constraint=False)
    name = models.CharField(
        verbose_name="상품명",
        max_length=255,
        help_text="주문 시점의 상품명을 저장합니다.",
    )
    price = models.PositiveIntegerField(
        verbose_name="상품가격", help_text="주문 시점의 가격을 저장합니다."
    )
    quantity = models.PositiveIntegerField(verbose_name="주문 수량")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# portone 결제와 관련된 필드 정의의
class AbstractPortonePayment(models.Model):
    class PayMethod(models.TextChoices):
        CARD = "card", "카드"

    class PayStatus(models.TextChoices):
        READY = "ready", "결제 준비"
        PAID = "paid", "결제 완료"
        CANCELED = "canceled", "결제 취소"
        FAILED = "failed", "결제 실패"

    meta = models.JSONField("포트원 결제내역", default=dict, editable=False)
    uid = models.UUIDField("쇼핑몰 결제식별자", default=uuid4, editable=False)
    name = models.CharField("결제명", max_length=200)
    desired_amount = models.PositiveIntegerField("결제금액", editable=False)
    buyer_name = models.CharField("구매자 이름", max_length=100, editable=False)
    buyer_email = models.EmailField("구매자 이메일", editable=False)
    pay_method = models.CharField(
        "결제 수단",
        choices=PayMethod.choices,
        max_length=20,
        default=PayMethod.CARD,
    )
    pay_status = models.CharField(
        "결제 상태",
        choices=PayStatus.choices,
        max_length=20,
        default=PayStatus.READY,
    )
    is_paid_ok = models.BooleanField(
        "결제 성공 여부", default=False, db_index=True, editable=False
    )

    @property
    def merchant_uid(self):
        return str(self.uid)

    @cached_property
    def api(self):
        return Iamport(
            imp_key=settings.PORTONE_API_KEY, imp_secret=settings.PORTONE_API_SECRET
        )

    def update(self):
        try:
            self.api.find(merchant_uid=self.merchant_uid)
        except (Iamport.ResponseError, Iamport.HttpError) as e:
            logger.error(str(e))
            raise Http404("포트원에서 결제 내역을 찾을 수 없습니다.")

        self.pay_status = self.meta["status"]
        self.is_paid_ok = self.api.is_paid(
            self.desired_amount, response=self.meta
        )  # 결제 금액과 실결제 금액이 일치한 지 확인하는 메서드

        # TODO: 결제완료지만 is_paid_ok=False => 결제 금액이 맞지 않은 경우

    class Meta:
        abstract = True


# 하나의 order에 대한 결제 시도
class OrderPayment(AbstractPortonePayment):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_constraint=False)

    @classmethod
    def create_by_order(cls, order: Order) -> "OrderPayment":
        payment = cls.objects.create(
            order=order,
            name=order.name,
            desired_amount=order.total_amount,
            buyer_name=order.user.get_full_name(),
            buyer_email=order.user.email,
        )
        return payment
