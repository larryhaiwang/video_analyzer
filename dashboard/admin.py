from django.contrib import admin

# Register your models here.
from dashboard.models import Files, VideoMetrics, ImageMetrics

admin.site.register(Files)
admin.site.register(VideoMetrics)
admin.site.register(ImageMetrics)