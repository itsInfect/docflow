from enum import StrEnum


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PREPROCESSING = "preprocessing"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    DUPLICATE_FILE = "duplicate_file"


class ProcessingRunStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    AWAITING_OCR = "awaiting_ocr"
    FAILED = "failed"


class RevisionStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"


TERMINAL_STATUSES = {
    DocumentStatus.REJECTED,
    DocumentStatus.DUPLICATE_FILE,
}
