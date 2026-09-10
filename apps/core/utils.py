"""
Core utility functions including file validation and pagination helpers.
"""

import os
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_file_upload(file):
    """
    Validates uploaded documents against size and extension restrictions.
    """
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)
    if file.size > max_size:
        raise ValidationError(f"File size exceeds limit of {max_size // (1024 * 1024)}MB.")

    ext = os.path.splitext(file.name)[1].lower()
    allowed_extensions = getattr(settings, 'ALLOWED_DOCUMENT_EXTENSIONS', ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'])
    if ext not in allowed_extensions:
        raise ValidationError(f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_extensions)}")
