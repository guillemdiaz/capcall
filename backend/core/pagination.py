from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    # Allows the customer to order more or fewer items (?page_size=50)
    page_size_query_param = "page_size"
    max_page_size = 100
