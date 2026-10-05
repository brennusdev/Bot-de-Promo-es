"""Schemas Pydantic para validação de entrada da API."""
from pydantic import BaseModel, Field, HttpUrl


class AdminLogin(BaseModel):
    """Corpo de login administrativo do dashboard."""
    password: str = Field(min_length=1)


class UserCreate(BaseModel):
    """Corpo de criação de usuário."""
    name: str | None = None
    phone: str = Field(min_length=1)


class AlertCreate(BaseModel):
    """Corpo de criação de alerta de preço."""
    product_id: int
    threshold_percent: float = Field(default=10.0, gt=0)


class ProductCreate(BaseModel):
    """Corpo de registro de produto por URL.

    ESTUDO: a URL é validada pelo Pydantic (http_url) — URLs malformadas
    nunca chegam ao coletor, que faria scraping em algo inválido.
    """
    url: HttpUrl
