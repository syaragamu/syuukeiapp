from django.urls import path
from .views import upload_file,download_file
from django.conf import settings
from django.conf.urls.static import static
app_name = 'syuukei'

urlpatterns = [
    path('upload/', upload_file, name='upload_file'),
    path('download/',download_file,name = 'download_file'),
]#+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)