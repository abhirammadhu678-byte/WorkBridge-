import os
import re
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


def validate_file_size(file_obj, max_mb):
    """Ensure file size is within the allowed limit."""
    max_bytes = max_mb * 1024 * 1024
    if hasattr(file_obj, 'size') and file_obj.size > max_bytes:
        raise ValidationError(f"File size exceeds the maximum limit of {max_mb}MB (uploaded file is {round(file_obj.size / (1024 * 1024), 2)}MB).")


def validate_file_extension(file_obj, allowed_extensions):
    """Ensure file has an approved extension."""
    name = getattr(file_obj, 'name', '')
    ext = os.path.splitext(name)[1].lower()
    if ext not in allowed_extensions:
        allowed_str = ", ".join(allowed_extensions)
        raise ValidationError(f"Unsupported file format '{ext}'. Allowed formats: {allowed_str}")


def validate_image_file(file_obj):
    """Validate user profile photos (JPG, PNG, WEBP, max 5MB)."""
    if not file_obj or not isinstance(file_obj, UploadedFile):
        return
    validate_file_extension(file_obj, ['.jpg', '.jpeg', '.png', '.webp'])
    validate_file_size(file_obj, 5)


def validate_document_file(file_obj):
    """Validate student resume documents (PDF, DOC, DOCX, max 10MB)."""
    if not file_obj or not isinstance(file_obj, UploadedFile):
        return
    validate_file_extension(file_obj, ['.pdf', '.doc', '.docx'])
    validate_file_size(file_obj, 10)


def validate_verification_doc(file_obj):
    """Validate college ID verification cards (PDF, JPG, PNG, WEBP, max 5MB)."""
    if not file_obj or not isinstance(file_obj, UploadedFile):
        return
    validate_file_extension(file_obj, ['.pdf', '.jpg', '.jpeg', '.png', '.webp'])
    validate_file_size(file_obj, 5)


def validate_portfolio_image(file_obj):
    """Validate portfolio project photos (JPG, PNG, WEBP, max 10MB)."""
    if not file_obj or not isinstance(file_obj, UploadedFile):
        return
    validate_file_extension(file_obj, ['.jpg', '.jpeg', '.png', '.webp'])
    validate_file_size(file_obj, 10)


def validate_video_file(file_obj):
    """Validate portfolio video reels (MP4, MOV, AVI, WEBM, MKV, max 25MB)."""
    if not file_obj or not isinstance(file_obj, UploadedFile):
        return
    validate_file_extension(file_obj, ['.mp4', '.mov', '.avi', '.webm', '.mkv'])
    validate_file_size(file_obj, 25)


def validate_mobile_number(value):
    """Validate phone number format (standard 10-digit Indian phone or +91/0 prefix format)."""
    if not value:
        return value
    clean_val = re.sub(r'[\s\-\(\)\+]', '', str(value))
    if clean_val.startswith('91') and len(clean_val) == 12:
        clean_val = clean_val[2:]
    elif clean_val.startswith('0') and len(clean_val) == 11:
        clean_val = clean_val[1:]
    if not re.match(r'^[6-9]\d{9}$', clean_val):
        raise ValidationError("Please enter a valid 10-digit mobile number starting with 6, 7, 8, or 9.")
    return clean_val

