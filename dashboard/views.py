from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from dashboard.models import Files, VideoMetrics, ImageMetrics, FILE_EXTENSION_TO_TYPE
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from dashboard.forms import FileUploadModelForm
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import datetime
import MLmodels.facial_analysis as fa
from django.conf import settings
from django.core.files import File
from django.template.defaultfilters import slugify
import os

# Type of files that are supported in analysis
SUPPORTED_FILE_TYPE ={
        'v':['.MP4',], # add more extensions for video
        't':[], # add more extensions for text
        'o':[], # add more extensions for voice
        'i':[], # add more extensions for image
        }


# In[]: Dashboard
'''
define a functional view that display summary information about user files. 
    # user login required
    # context - 
        * my_files: the list of Files record that uploaded by logged in user.
        * file_count: the total number of files uploaded by user. 0 is stored if there is no file.
        * last_upload_file: the name of the last uploaded file. None is stored if there is no file.
        * last_upload_datetime: the datetime of the last uploaded file. None is stored if there is no file.
        * user: the logged in user from User model.
        * num_visits: the number of site visit in a session.
    # template - index.html
'''
@login_required
def index_view(request):
    # retrieve all files of logged in user
    my_files = Files.objects.filter(upload_by=request.user).order_by('-upload_datetime')
    file_count = my_files.count()
    # in case of no file 
    if file_count == 0:
        context = {'my_files': my_files,
                   'file_count': file_count,
                   'last_upload_file': None,
                   'last_upload_datetime': None,
                   'user': request.user}
    # in case of at lease one file
    else:       
        last_upload_file = my_files[0].name
        last_upload_datetime = my_files[0].upload_datetime
        context = {'my_files': my_files,
                   'file_count': file_count,
                   'last_upload_file': last_upload_file,
                   'last_upload_datetime': last_upload_datetime,
                   'user': request.user}
    # count number of visits in session
    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits
    # add number of visits to context
    context['num_visits'] = num_visits
    
    return render(request, 'index.html', context)

# In[]: File upload
'''
define a functional view for user to upload file.
    # user login required
    # context -
        * file: the new created Files record
        * form: the upload file form
        * user: the logged in user from User model
    # template - uploadfile.html
'''
@login_required
def file_upload_view(request):
    if request.method == 'POST':
        # requst.FILES should be included 
        upload_form = FileUploadModelForm(request.POST, request.FILES)
        if upload_form.is_valid():
            # create a new file in Files model. id and upload_datetime are automatically populated
            uploadfile = Files()
            uploadfile.name = upload_form.cleaned_data['name']
            uploadfile.file = upload_form.cleaned_data['file']
            uploadfile.upload_by = request.user
            uploadfile.pop_file_type()
            uploadfile.save()
            # redirect to file upload sucess page
            return HttpResponseRedirect(reverse('uploadfile_done', args=[uploadfile.id]))
    else:
        upload_form = FileUploadModelForm()
    
    context = {'form':upload_form}
    return render(request, 'upload_file.html', context)

'''
define a functional view for success file upload.
    # user login required
    # context -
        * file: the Files record created by upload
    # template - upload_file_done.html
'''
from django.shortcuts import get_object_or_404

@login_required
def file_upload_sucess_view(request, pk):
    # retrieve the Files record
    file = get_object_or_404(Files, pk=pk)
    # respond with file only if the login user is the owner
    if file.upload_by == request.user:
        context = {'file':file}
    else:
        context = {'file':None}
    return render(request, 'upload_file_done.html', context)

# In[]: File list
'''
define a class view for user to review his/her uploaded files.
    # user login required
    # context - 
        * my_files: the list of files uploaded by the user (including deleted files)
        * file_count: the number of files uploaded by user
        * delete_count: the number of deleted files uploaded by user
    # template - my_files.html
'''
class MyFilesListView(LoginRequiredMixin, generic.ListView):
    model = Files
    context_object_name = 'my_files'
    template_name = 'my_files.html'
    
    # define query set
    def get_queryset(self):
        my_files = Files.objects.filter(upload_by=self.request.user).order_by('-upload_datetime')
        # do not return actual file to browser if it is deleted
        for file in my_files:
            if file.deleted:
#                file.file = 'removed'
                pass
        return my_files
    
    # add counts to context:
    def get_context_data(self, **kwargs):
        context = super(MyFilesListView, self).get_context_data(**kwargs)
        # list of user uploaded files
        my_files = Files.objects.filter(upload_by=self.request.user)
        context['file_count'] = my_files.count()
        context['delete_count'] = my_files.filter(deleted=True).count()
        return context

'''
define a class view for staff user to review all uploaded files.
    # user login required
    # permission - dashboard.can_view_any_file
    # context - 
        * all_files: the list of files uploaded by any user (including deleted files)
        * file_count: the number of files uploaded
        * delete_count: the number of deleted files
    # template - all_files.html
'''
class AllFilesListView(PermissionRequiredMixin, generic.ListView):
    model = Files
    context_object_name = 'all_files'
    template_name = 'all_files.html'
    permission_required = 'dashboard.can_view_any_file'
    
    # define query set
    def get_queryset(self):
        my_files = Files.objects.all().order_by('-upload_datetime')
        # do not return actual file to browser if it is deleted
        for file in my_files:
            if file.deleted:
#                file.file = 'removed'
                pass
        return my_files
    
    # add counts to context:
    def get_context_data(self, **kwargs):
        context = super(AllFilesListView, self).get_context_data(**kwargs)
        # list of user uploaded files
        my_files = Files.objects.all()
        context['file_count'] = my_files.count()
        context['delete_count'] = my_files.filter(deleted=True).count()
        return context   

# In[]: File delete
'''
define a function view for user to soft delete a file.
    # login required
    # context -
        * delete_file: the file to be deleted
        * form: the FileDeleteForm
        * has_perm: whether user has access to delete the file
    # template: delete_file.html
'''
@login_required
def file_delete_view(request, pk):
    # retrieve the Files record
    delete_file = get_object_or_404(Files, pk=pk)
    # For user to delete a file, he/she has to be the owner or has permission to delete any file
    has_perm = delete_file.upload_by == request.user or request.user.has_perm('dashboard.can_delete_any_file')
    if request.method=='POST':
        # soft delete the file only if deleted = True and user has proper permission
        if request.POST['deleted']=='T' and has_perm:
                delete_file.deleted = True
                delete_file.delete_by = request.user
                delete_file.delete_datetime = datetime.date.today()
                delete_file.save()
                return HttpResponseRedirect(reverse('myfiles'))
    else:
        pass
    
    # if user does not have access to view the file, prevent sending delete_file to template
    if delete_file.upload_by == request.user or request.user.has_perm('dashboard.can_view_any_file'):
        context=  {'delete_file':delete_file,
                   'has_perm':has_perm}
    else:
        context=  {'delete_file':None,
               'has_perm':has_perm}
    return render(request, 'delete_file.html', context)

# In[]: waiting page
'''
define a function view to show progress of background calculation
    # login required
    # input
        * calc_url: specify the type of analysis to perform on file
        * pk: the unique id of the file
    # context
        * calc_url: same as input
        * pk: same as input
    # template: wait_for_calculation.html
'''
# need to add more security to prevent direct page visit
@login_required
def wait_for_calculation_view(request, calc_url, pk):
    return render(request, 'wait_for_calculation.html', {'calc_url': calc_url, 'pk':pk})

# In[]: file details
'''
define a functional view for user to view file contents, request analysis and view analysis results if there is any.
    # login_required
    # input
        * pk: primary key for the file
    # context
        * file: the Files instance retrieved from data model
        * file_metrics: the metrics instances retrieved from data model
        * errors: a list of error messages
    # template: 'video_details.html' or 'image_details.html' or 'file_details_generic.html' (based on the type of file)
'''
@login_required
def file_details_view(request, pk):
    # retrieve file
    file = get_object_or_404(Files, pk=pk)
    # check user access: only owner and user with 'can_view_any_file' access can see video details.
    perm = file.upload_by==request.user or request.user.has_perm('dashboard.can_view_any_file')
    # remove video if user has no permission
    if not perm:
        file = None
    # based on the type of file, retrieve metric instance, calculation method, and template
    file_metrics = None
    calc_method = None
    template = 'file_details_generic.html'
    errors = []
    if file is not None:
        if file.file_type == 'v': # video
            if file.count_analyzed != 0:
                file_metrics = VideoMetrics.objects.filter(file_id=file.id).order_by('-create_datetime')[0]
            calc_method = 'video_analysis'
            template = 'video_details.html'
        elif file.file_type == 'i': # image
            if file.count_analyzed != 0:
                file_metrics = ImageMetrics.objects.filter(file_id=file.id).order_by('-create_datetime')[0]
            calc_method = 'image_analysis'
            template = 'image_details.html'
        elif file.file_type == 't':
            template = 'text_details.html'
            pass
        elif file.file_type == 'o':
            pass
        else:
            error_string = ('<p>File format %s is no recognized. Try the followings file types:</p>'
                            '<ul>'
                                '<li>Video: %s</li>'
                                '<li>Text: %s</li>'
                                '<li>Voice: %s</li>'
                                '<li>Image: %s</li>'
                            '</ul>')
            errors.append(error_string % (file.extension(), ', '.join(FILE_EXTENSION_TO_TYPE['v']), ', '.join(FILE_EXTENSION_TO_TYPE['t']), 
                                          ', '.join(FILE_EXTENSION_TO_TYPE['o']), ', '.join(FILE_EXTENSION_TO_TYPE['i'])))
    # analyze the file if requested, has permission and file is no unclassified
    if request.method=='POST' and request.POST['analyze']=='T' and perm and file.file_type != 'u':
        # check whether file format is acceptable
        if file.extension() in SUPPORTED_FILE_TYPE[file.file_type]:
            # redirect to waiting page and image video analysis
            return HttpResponseRedirect(reverse('waiting', args=(calc_method, pk)))
        else:
            errors.append('File format "%s" is not supported at the moment. Try the followings file types: %s.' % (file.extension(), ', '.join(SUPPORTED_FILE_TYPE[file.file_type])))
    
    context = {'file':file,
               'file_metrics':file_metrics,
               'errors': errors,
               } 
    return render(request, template, context)

# In[]: video analysis
'''
define a calculation view to analyze video
    # login_required
    # input
        * pk: the unique id of the file
    # context
        * status: indicate whether the calculation is successful 's', or contains errors 'e'.
        * errors: the error messages from calculation
'''

# need to add more security to prevent direct page visit
@login_required
def video_analysis_calc(request, pk):
    # initialization and retrieve video
#    video = get_object_or_404(Files, pk=pk, file_type__exact='v')
    video = get_object_or_404(Files, pk=pk)
    status = 's'
    errors = []
    # the path to save marked video; slugify() converts string to URL and filename friendly
    save_name= '%s_analyzed.mp4' % (slugify(video.name))
    temp_path = settings.MEDIA_ROOT + '/__tempfile/%s/%s' % (video.upload_by.username, save_name)
    
    # get facial trackers of the video
    summary, face_tracker, tracker_errors = fa.face_68_tracker(video.file.path, verbose=False, save_video=True, save_path=temp_path)
    # conduct further analysis if facial tracker is successfull run. Otherwise append error messages.
    if summary != {}:
        # analyze blinking
        eye_aspect_ratio, blink_count, blink_errors = fa.detect_blink(summary, face_tracker)
        errors.append(blink_errors)
    else:
        status = 'e'
        errors.append(tracker_errors)
            
    # store output in VideoMetrics model as a new entry
    video_metrics = VideoMetrics()
    video_metrics.file_id = video
    # save marked_video and remove temporary file. If failed then write to error messages.
    try:
        with open(temp_path+'/dummy/', mode='rb') as f:
            marked_file = File(f)
            video_metrics.marked_video.save(save_name, marked_file, save=True)
        os.remove(temp_path)
    except:
        status = 'e'
        errors.append('An error prevent processed video content to be saved. Only analysis metrics are available.')

    video_metrics.calc_status = status
    video_metrics.frame_num = summary['total_frame']
    video_metrics.fps = summary['fps']
    video_metrics.blink_count = blink_count[-1]
    video.count_analyzed += 1
    
    video_metrics.save()
    video.save()
    
    data = {'status': status, 'errors':errors}
    return JsonResponse(data)

