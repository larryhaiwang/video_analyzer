from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    """
    S3 storage for static files (such as CSS, etc.)
    """
    if not settings.DEBUG:
        location = settings.AWS_STATIC_LOCATION


class PublicMediaStorage(S3Boto3Storage):
    """
    Use this class in any models.File(storage=PublicMediaStorage() upload_to=...) to ensure the
    file is uploaded to S3 into the PUBLIC space

    Public generates url's that are publicly accessible and do not expire
    """
    location = settings.AWS_PUBLIC_MEDIA_LOCATION
    file_overwrite = False


class PrivateMediaStorage(S3Boto3Storage):
    """
    Use this class in any models.File(storage=PrivateMediaStorage() upload_to=...) to ensure the
    file is uploaded to S3 into the PRIVATE space

    Private generates url's that are only valid for one hour
    """
    location = settings.AWS_PRIVATE_MEDIA_LOCATION
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False