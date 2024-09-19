"""Enums and Constants for PDF Gen Project"""

from enum import Enum, auto


# styling constants
MAIN_TITLE_Y = 750
START_Y = 700
TITLE_X = 15
INPUT_BOX_X = 140
INPUT_BOX_WIDTH = 612 - 30
UNIT_WIDTH = (612 - 30)/3
MARGIN_BOTTOM = 50
ONE_LINE_HEIGHT = 15

# schemas Root Folder
SCHEMAS_ROOT_FOLDER = 'business_schemas'


"""Enum - PDF Module"""
class PdfModule(Enum):
    HEADER = auto()
    CERTIFICATION = auto()
    TOP_NOTE = auto()
    FOOTER = auto()
    EFFECTIVE_DATE = auto()


"""Enum - PDF Config Common Option"""
class PdfConfigOption(Enum):
    EXTRA_MODULE = auto()
    FEE_CAL_PATH = auto()
    FORM_TITLE = auto()
    FOOTER_INFO = auto()
    NUM_OF_CERTIFICATION = auto()
    SECTION_ORDER = auto()
    TOP_NOTE_INFO = auto()
    FILING_NAME_IN_EFFECTIVE_DATE = auto(),
    EXCLUDED_KEYS = auto(),
    COMPONENT_CONFIGS = auto(),
    CERTIFICATION_INFO = auto()


"""Enum - PDF Font Style"""
class PdfFontStyle(Enum):
    REGULAR = 'Helvetica'
    ITALIC = 'Helvetica-Oblique'
    BOLD = 'Helvetica-Bold'


"""Enum - PDF Font Size"""
class PdfFontSize(Enum):
    FILE_TITLE = 18
    CONTENT = 10
    SECTION_TITLE = 12
    SMALL_NOTE = 6
    TITLE_CONTACT_INFO = 8
    BOLD_NOTE = 9


"""Enum - Generable PDF File"""
class GenerableItem(Enum):
    AGM_LOCATION_CHANGE = 'agm_location_change'
    REGULAR_AMALGAMATION_APPLICATION = 'amalgamation_application'
    # Options below DO NOT have configs
    AGM_EXTENSION = 'agm_extension' 
    ALTERATION = 'alteration'
    ANNUAL_REPORT = 'annual_report'
    CHANGE_OF_ADDRESS = 'change_of_address'
    CHANGE_OF_DIRECTORS = 'change_of_directors'
    CHANGE_OF_NAME = 'change_of_name'
    CHANGE_OF_REGISTRATION = 'change_of_registration'
    CONSENT_CONTINUATION_OUT = 'consent_continuation_out'
    CONTINUATION_IN = 'continuation_in'
    CONTINUATION_OUT = 'continuation_out'
    CORRECTION = 'correction'
    COURT_ORDER = 'court_order'
    DISSOLUTION = 'dissolution'
    INCORPORATION_APPLICATION = 'incorporation_application'
    REGISTRATION = 'registration'
    RESTORATION = 'restoration'
    SPECIAL_RESOLUTION = 'special_resolution'
    TRANSITION = 'transition'
    # UNMANAGED = 'unmanaged' # ingore this one


"""Enum - Text Field Size"""
class FieldSize(Enum):
    SMALL = UNIT_WIDTH
    MID = UNIT_WIDTH * 2
    LARGE = UNIT_WIDTH * 3

# Form footer info configuration
# need to remove this when finalizing the project, it's in pdf_configs now
FORM_FOOTER_INFO = {
    GenerableItem.REGULAR_AMALGAMATION_APPLICATION: "FORM 13 LTD (SEP 2017)",
}
