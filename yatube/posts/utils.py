from django.conf import settings

from django.core.paginator import Paginator


def list_page(list, request):
    paginator = Paginator(list, settings.POSTS_TO_DISPLAY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
