"""
URL configuration for surveillance_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.conf.urls import handler400, handler403, handler404, handler500

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # JWT authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API endpoints
    path('api/auth/', include('users.urls')),
    path('api/sessions/', include('exam_sessions.urls')),
    path('api/violations/', include('violations.urls')),
    path('api/blockchain/', include('blockchain.urls')),
    path('api/monitoring/', include('monitoring.urls')),
    path('api/analytics/', include('analytics.urls')),
    
    # Web interface
    path('', include('dashboard.urls')),
    path('auth/', include('users.web_urls')),
    path('monitoring/', include('monitoring.web_urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# Custom admin site configuration
admin.site.site_header = "Surveillance System Administration"
admin.site.site_title = "Surveillance System Admin"
admin.site.index_title = "Welcome to Surveillance System Administration"

handler400 = 'surveillance_system.views.bad_request_view'
handler403 = 'surveillance_system.views.permission_denied_view'
handler404 = 'surveillance_system.views.page_not_found_view'
handler500 = 'surveillance_system.views.server_error_view' 