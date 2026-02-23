from typing import List, TypeVar, Generic
from pydantic import BaseModel
from math import ceil

T = TypeVar('T')

class PaginationMeta(BaseModel):
    """Pagination metadata"""
    total: int
    page: int
    page_size: int
    total_pages: int

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    pagination: PaginationMeta

def create_pagination_meta(total: int, skip: int, limit: int) -> PaginationMeta:
    """Helper to create pagination metadata"""
    current_page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = ceil(total / limit) if limit > 0 else 1
    
    return PaginationMeta(
        total=total,
        page=current_page,
        page_size=limit,
        total_pages=total_pages
    )
