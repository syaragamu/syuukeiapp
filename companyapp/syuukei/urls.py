from django.urls import path
from .views import upload_file,download_syuukei_file,download_seibann_file
from django.conf import settings
from django.conf.urls.static import static
app_name = 'syuukei'

urlpatterns = [
    path('upload/', upload_file, name='upload_file'),
    path('download/syuukei',download_syuukei_file,name = 'download_syuukei_file'),
    path('download/seibann',download_seibann_file,name = 'download_seibann_file'),
]#+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)