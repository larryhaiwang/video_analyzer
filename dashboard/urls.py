from django.urls import path
from dashboard import views

# define URL patterns for catalog app
urlpatterns = [
        # index page that shows the summary of files
        path('', views.index_view, name='index'),
        
        # file upload page that user uploads files
        path('upload/', views.file_upload_view, name='uploadfile'),
        
        # file upload sucess page that indicates success upload and display file details 
        path('upload/done/<uuid:pk>', views.file_upload_sucess_view, name='uploadfile_done'),
        
        # my file list page that lists the files uploaded by logged in user
        path('myfiles/', views.MyFilesListView.as_view(), name='myfiles'),
        
        # all file list page that lists all files uploaded by users
        path('allfiles/', views.AllFilesListView.as_view(), name='allfiles'),
        
        # file delete page that use can delete a file
        path('file/delete/<uuid:pk>', views.file_delete_view, name='deletefile'),
        
        # a wait page displayed to use while waiting for backend calculation
        # pass calc_url to indicate the type of analysis to do on file
        path('waiting/<str:calc_url>/<uuid:pk>', views.wait_for_calculation_view, name='waiting'),

        # view file page that show unclassified files
        path('file/details/<uuid:pk>', views.file_details_view, name='filedetails'),
        
        # view file page that shows video contents and analysis results
#        path('file/video/details/<uuid:pk>', views.video_details_view, name='videodetails'),
        
        # ajax call to analyze video file in backend. The name will be used in calc_url argument in wasting page
        path('__calculation/video_analysis/<uuid:pk>', views.video_analysis_calc, name='video_analysis'),
        
        # view file page that shows image contents and analysis results
#        path('file/image/details/<uuid:pk>', views.image_details_view, name='imagedetails'),
        
#        # ajax call to analyze image file in backend. The name will be used in calc_url argument in wasting page
#        path('__calculation/image_analysis/<uuid:pk>', views.image_analysis_calc, name='image_analysis'),
        
        ]