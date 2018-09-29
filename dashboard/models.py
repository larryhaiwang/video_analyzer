from django.db import models
import uuid
from django.contrib.auth.models import User
import os

# In[]
# always in upper case
FILE_EXTENSION_TO_TYPE ={
        'v':['.MP4',], # add more extensions for video
        't':['.TXT','.PDF',], # add more extensions for text
        'o':[], # add more extensions for voice
        'i':['.JPG','.PNG','.GIF',], # add more extensions for image
        }

# In[]
'''
define a model to store user uploaded files. following fields are included:
    # fields
        * id: uuid primary key
        * name: the name of the file (less than 100 characters)
        * file: FileField for the file
        * file_type: indicate the type of uploaded file; default value is 'u'.
            'v': video
            't': text
            'o': voice
            'i': image
            'u': unclassified
        * upload_by: foregin key to the user who uploaded the file
        * upload_datetime: the datetime of about when the file is uploaded
        * deleted: a boolean indicating soft deletion
        * deleted_by: foregin key to the user who deleted the file
        * delete_datetime: the datetime when the file the deleted
    # methods:
        * extension(): return uploaded file extension, including beginning dot. e.g. ".txt"
        * pop_file_type(): based on file extension, populate file_type of the instance and return the file_type value, 
'''
def user_upload_path(instance, filename):
    # file will be uploaded to uploadfiles/<username>/<filename>
    return 'uploadfiles/%s/%s' % (instance.upload_by.username, filename)

class Files(models.Model):
    # fields
    id = models.UUIDField(verbose_name='Unique ID', primary_key=True, default=uuid.uuid4, help_text='Unique ID for each uploaded file')
    name = models.CharField(verbose_name='File Name', max_length=100, help_text='Enter a name for the file (less than 100 characters)')
    file = models.FileField(verbose_name='Uploaded File', upload_to=user_upload_path)
    FILE_TYPE_CHOICES = (
            ('v','Video'),
            ('t','Text'),
            ('o','Voice'),
            ('i','Image'),
            ('u','Unclassified'),
            )
    file_type = models.CharField(verbose_name='File Type', max_length=1, choices=FILE_TYPE_CHOICES, default='u')
    # since there are two foreign key to User model, related_name is required to distinguish the fields.
    upload_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='upload_by')
    upload_datetime = models.DateTimeField(verbose_name='Upload Datetime', auto_now_add=True) # auto_now_add=True stores the datetime when a new record is created. 
    deleted = models.BooleanField(verbose_name='Is Deleted', default = False)
    delete_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='delete_by')
    delete_datetime = models.DateTimeField(verbose_name='Deletion Datetime', null=True, blank=True)
    count_analyzed = models.IntegerField(verbose_name='Count of Analysis', default=0)
    
    # meta
    class Meta:
        ordering = ['-upload_datetime'] # ording by descending upload datetime
        permissions = (('can_view_any_file', 'View Any File'), # can view any file across all users
                       ('can_delete_any_file', 'Delete Any File'), # can delete any file across all users
                )
    # methods
    def __str__(self):
        string = '%s (%s)' % (self.name, self.upload_by)
        return string
    
    # get file extention
    def extension(self):
        filename, extension = os.path.splitext(self.file.name)
        return extension.upper()

    # populate and return file_type
    def pop_file_type(self):
        file_type = 'u'
        ext = self.extension()
        # iterate through FILE_EXTENSION_TO_TYPE for match
        for key in FILE_EXTENSION_TO_TYPE:
            if ext in FILE_EXTENSION_TO_TYPE[key]:
                file_type = key
                break
        # save file_type in model
        self.file_type = file_type
        self.save()
        # return file_type
        return file_type
            

# In[]
'''
define a model to store analysis results of videos. following fields are included:
    # id - uuid primary key
    # file_id - foregin key to Files model
    # calc_status - indicate whether the metrics are resulted from success analysis. 
        * 's' - Success
        * 'e' - Error
    # marked_video - post process video
    # frame_num - number of frames in video
    # fps - frame per second
    # blink_count - number of blinks in the video
    # transcript - the transcript of the speach in the video
    # create_datetime - the datetime when the record is created
'''
def marked_file_path(instance, filename):
    # file will be uploaded to uploadfiles/<username>/<filename>
    return 'markedfiles/%s/%s' % (instance.file_id.upload_by.username, filename)

class VideoMetrics(models.Model):
    # fields
    id = models.UUIDField(verbose_name='Unique ID', primary_key=True, default=uuid.uuid4, help_text='Unique Id for each file analysis record')
    file_id = models.ForeignKey(Files, on_delete=models.SET_NULL, null=True, blank=True)
    calc_status = models.CharField(verbose_name='Analysis Status', max_length=1, choices=(('s','Success'),('e','Error')), null=True)
    marked_video = models.FileField(verbose_name='Marked Video', upload_to=marked_file_path, null=True)
    frame_num = models.IntegerField(verbose_name='Number of Frames', null=True)
    fps = models.FloatField(verbose_name='Frame per Second', null=True)
    blink_count = models.IntegerField(verbose_name='Number of Blinks', help_text='Number of blinks in the video', null=True)
    transcript = models.TextField(verbose_name='Video Transcript', max_length=10000, help_text='Transcript of the speach in the video', null=True, blank=True)
    create_datetime = models.DateTimeField(verbose_name='Creation Datetime', auto_now_add=True)
    
    # meta
    class Meta:
        ordering = ['-create_datetime']
        permissions = (('can_view_any_metric', 'View Any Metric'), # can view any metric across all users
                       ('can_edit_any_metric', 'Edit Any Metric'), # can update or delete any metric across all users
                )
    
    # methods
    def __str__(self):
        string = '%s (%s)' % (self.file_id, self.create_datetime)
        return string

# In[]
'''
define a model to store analysis results of images.
    # fields:
        * id: uuid primary key
        * file_id: foreign key to Files model
        * calc_status - indicate whether the metrics are resulted from success analysis.
        * marked_image: post process image
        * created_datetime: the dateime when the record is created
'''
class ImageMetrics(models.Model):
    # fields
    id = models.UUIDField(verbose_name='Unique ID', primary_key=True, default=uuid.uuid4, help_text='Unique Id for each file analysis record')
    file_id = models.ForeignKey(Files, on_delete=models.SET_NULL, null=True, blank=True)
    calc_status = models.CharField(verbose_name='Analysis Status', max_length=1, choices=(('s','Success'),('e','Error')), null=True)
    marked_image = models.FileField(verbose_name='Marked Image', upload_to=marked_file_path, null=True)
    create_datetime = models.DateTimeField(verbose_name='Creation Datetime', auto_now_add=True)
    
    # meta
    class Meta:
        ordering = ['-create_datetime']
    
    # methods
    def __str__(self):
        string = '%s (%s)' % (self.file_id, self.create_datetime)
        return string