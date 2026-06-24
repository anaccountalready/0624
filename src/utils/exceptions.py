class PdfToEpubError(Exception):
    pass


class PDFParseError(PdfToEpubError):
    pass


class PDFEncryptedError(PDFParseError):
    pass


class PDFEmptyError(PDFParseError):
    pass


class PDFImageExtractionError(PDFParseError):
    pass


class EPUBBuildError(PdfToEpubError):
    pass


class EPUBEmptyError(EPUBBuildError):
    pass


class EPUBImageError(EPUBBuildError):
    pass


class EPUBWriteError(EPUBBuildError):
    pass


class TaskError(PdfToEpubError):
    pass


class TaskTimeoutError(TaskError):
    pass


class ConfigError(PdfToEpubError):
    pass


class OCRError(PdfToEpubError):
    pass


class FormatNotSupportedError(PdfToEpubError):
    pass