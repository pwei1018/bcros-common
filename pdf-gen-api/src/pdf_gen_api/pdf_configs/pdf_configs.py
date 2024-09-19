"""PDF Generation Configurations"""

from ..resources.utils import (
    GenerableItem, PdfConfigOption, PdfModule, 
    PdfFontSize, PdfFontStyle
)

from enum import Enum
from datetime import date

##### commonly used config keys #####
class CommonConfigKeys(Enum):
    SECTION = 'sectionTitle',
    ITEM = 'itemTitle'


###### Helper functions ######
def _create_top_note_config(left_column_info:str, right_column_info:str) -> dict:
    """ output will be a dict of 2 items
        in each item, will be a list of strings, 
        in each list, each list_item will be one line in a paragraph
    """
    top_note_config = {}
    top_note_config['left_column'] = left_column_info.split('\n')
    top_note_config['right_column'] = right_column_info.split('\n')
    return top_note_config


def _create_component_config(label_name:str, font_size:PdfFontSize=PdfFontSize.CONTENT, font_style:PdfFontStyle=PdfFontStyle.REGULAR, length:int=None, num_of_item:int=1) -> dict:
    component_config = {}
    component_config['label'] = label_name
    styles_dict = {}
    styles_dict['length'] = length
    styles_dict['font_size'] = font_size
    styles_dict['font_style'] = font_style
    component_config['styles'] = styles_dict
    component_config['reps'] = num_of_item
    return component_config


##### Common Excluded Keys #####
common_excluded_keys = [
        '$schema',
        '$id',
        'dependencies',
        'definitions',
        'required',
        'if'
]


##### Default Content for PDFs without any configurations #####
default_top_notes_content = _create_top_note_config('DO NOT MAIL THIS FORM to BC Registry Services \nunless you are instructed to do so by registry staff.', 'Questions regarding the collection, use and disclosure \nof personal information can be directed to the \n Manager of Registries Operations at 1 877 526-1526, \nPO Box 9431 Stn Prov Govt, Victoria BC V8W 9V3.')


default_render_order = [ # used for guiding rendering , when there is no configs for module order
    PdfModule.HEADER,
    PdfModule.TOP_NOTE,
    'any_main_content_sections' # serves as a flag 
]

today = date.today()
default_footer_info = today.strftime("%b %Y").upper()


##### Common Configs #####
# configs used in multiple places
common_address = {
    'addressCity': _create_component_config('CITY', length=40),
    'addressCountry': _create_component_config('COUNTRY'),
    'addressRegion': _create_component_config('PROVINCE/STATE', length=2),
    'deliveryInstructions': _create_component_config('DELIVERY INSTRUCTIONS', length=80),
    'postalCode': _create_component_config('POSTAL CODE/ZIP CODE', length=15),
    'streetAddress': _create_component_config('STREET ADDRESS', length=50),
    'streetAddressAdditional': _create_component_config('STREET ADDRESS ADDITIONAL', length=50),
}
common_deliveryAddress = {
    CommonConfigKeys.ITEM: _create_component_config('DELIVERY ADDRESS'),
    **common_address
}
common_mailingAddress = {
    CommonConfigKeys.ITEM: _create_component_config('MAILING ADDRESS'),
    **common_address
}


##### Common Extra Modules #####
common_extra_modules = {
    PdfModule.HEADER,
    PdfModule.TOP_NOTE,
    PdfModule.FOOTER
}




##### Configs #####
# Config for each filing
pdf_configs = {
    # config for AGM Location Change
    GenerableItem.AGM_LOCATION_CHANGE: {
        PdfConfigOption.EXTRA_MODULE: common_extra_modules.union({PdfModule.CERTIFICATION}),
        PdfConfigOption.FORM_TITLE: 'AGM LOCATION CHANGE',
        PdfConfigOption.TOP_NOTE_INFO: _create_top_note_config('DO NOT MAIL THIS FORM to BC Registry Services\nunless you are instructed to do so by registry staff. \nThe Regulation under the Business Corporations Act \nrequires the electronic version of this form to be filed \non the Internet at www.bcregistry.ca/business\n\nIf you are instructed by registry staff to mail this form to \nthe Corporate Registry, submit this form with a cheque \nor money order made payable to the Minister of Finance, \nor provide the registry with authorization to debit \nthe fee from your BC OnLine Deposit Account.\nPlease pay in Canadian dollars or in the equivalent amount \nof US funds.', 'Freedom of Information and Protection of Privacy Act (FOIPPA): \nPersonal information provided on this form is collected,\nused and disclosed under the authority of the FOIPPA and\nthe Business Corporations Act for the purposes of assessment.\nQuestions regarding the collection, use and disclosure of\npersonal information can be directed to the Manager of\nRegistries Operations at 1 877 526-1526, PO Box 9431 Stn Prov\nGovt, Victoria BC V8W 9V3'),
        PdfConfigOption.FOOTER_INFO: 'FORM DEMO (JUL 2024)',
        PdfConfigOption.NUM_OF_CERTIFICATION: 1,
        PdfConfigOption.EXCLUDED_KEYS: common_excluded_keys,
        PdfConfigOption.CERTIFICATION_INFO: {
            'title': 'CERTIFICATION',
            'description': 'I have read this form and found it to be correct.',
            'note': 'This form must be signed by an authorized signing authority for the company.',
            'fields': ['NAME', 'SIGNATURE', 'DATE'],
            'date_format': 'YYYY/MM/DD'
        },
        PdfConfigOption.SECTION_ORDER: [
            PdfModule.HEADER,
            PdfModule.TOP_NOTE,
            'year',
            'reason',
            'agmLocation',
            PdfModule.CERTIFICATION
        ],
        PdfConfigOption.COMPONENT_CONFIGS: {
            'year': {
                CommonConfigKeys.SECTION: _create_component_config('AGM Year', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD, length=10)
            },
            'reason': {
                CommonConfigKeys.SECTION: _create_component_config('Reason of Change Location', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD, length=2000)
            },
            'agmLocation': {
                CommonConfigKeys.SECTION: _create_component_config('AGM Location', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD, length=400)
            }
        }
        
    },
    # config for Regular Amalgamation Application
    GenerableItem.REGULAR_AMALGAMATION_APPLICATION: {
        PdfConfigOption.EXTRA_MODULE: common_extra_modules.union({PdfModule.CERTIFICATION, PdfModule.EFFECTIVE_DATE}),
        PdfConfigOption.FORM_TITLE: 'AMALGAMATION APPLICATION',
        PdfConfigOption.TOP_NOTE_INFO: _create_top_note_config('DO NOT MAIL THIS FORM to BC Registry Services\nunless you are instructed to do so by registry staff.\nThe Regulation under the Business Corporations Act \nrequires the electronic version of this form to be filed \non the Internet at www.corporateonline.gov.bc.ca ', 'Freedom of Information and Protection of Privacy Act (FOIPPA):\nPersonal information provided on this form is collected, used and \ndisclosed under the authority of the FOIPPA and the Business \nCorporations Act for the purposes of assessment. Questions regarding \nthe collection, use and disclosure of personal information can be \ndirected to the Manager of Registries Operations at 1 877 526-1526, \nPO Box 9431 Stn Prov Govt, Victoria BC V8W 9V3.'), #dividing lines using \n
        PdfConfigOption.FOOTER_INFO: 'FORM 13 LTD (SEP 2017)',
        PdfConfigOption.NUM_OF_CERTIFICATION: 5,
        PdfConfigOption.FILING_NAME_IN_EFFECTIVE_DATE:'amalgamation',
        PdfConfigOption.EXCLUDED_KEYS: common_excluded_keys + ['if', 'title'],
        PdfConfigOption.CERTIFICATION_INFO: {
            'title': 'CERTIFICATION',
            'description': 'I have read this form and found it to be correct.',
            'note': 'This form must be signed by an authorized signing authority for the company.',
            'fields': ['NAME', 'SIGNATURE', 'DATE'],
            'date_format': 'YYYY/MM/DD'
        },
        PdfConfigOption.SECTION_ORDER: [ #Footer won't be in the list since it's rendering logic will be add at the end of every page
            PdfModule.HEADER,
            PdfModule.TOP_NOTE,
            'type', #the one has an enum of regular, vertical, horizontal
            'nameRequest',
            'courtApproval',
            'courtOrder',
            PdfModule.EFFECTIVE_DATE,
            'amalgamatingBusinesses',
            'contactPoint',
            PdfModule.CERTIFICATION,
            'nameTranslations',
            'parties',
            'offices',
            'shareStructure',
        ],
        PdfConfigOption.COMPONENT_CONFIGS: {
            'type': {
                CommonConfigKeys.SECTION: _create_component_config('THE TYPE OF AMALGAMATION', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD),
            },
            'parties': {
                CommonConfigKeys.SECTION: _create_component_config('DIRECTOR NAME(S) AND ADDRESS(ES)', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD, num_of_item=4), # this config is for the section title
                'deliveryAddress': common_deliveryAddress,
                'mailingAddress': common_mailingAddress,
                'officer': {
                    CommonConfigKeys.ITEM: _create_component_config('OFFICER'),
                    'email': _create_component_config('EMAIL'),
                    'firstName': _create_component_config('FIRST NAME', length=30),
                    'identifier': _create_component_config('IDENTIFIER(if available for Organization)'),
                    'lastName': _create_component_config('LAST NAME', length=30),
                    'middleInitial': _create_component_config('MIDDLE NAME', length=30),
                    'organizationName': _create_component_config('ORGANIZATION NAME', length=150),
                    'partyType': _create_component_config('PARTY TYPE'),
                },                
                'roles': {
                    CommonConfigKeys.ITEM: _create_component_config('ROLES', num_of_item=3),
                    'appointmentDate': _create_component_config('APPOINTMENT DATE'),
                    'cessationDate': _create_component_config('CESSATION DATE'),
                    'roleType': _create_component_config('ROLE TYPE'),
                },
                'then': None # --> ignore what's in it               
            },
            'nameTranslations': {
                CommonConfigKeys.SECTION: _create_component_config('TRANSLATIONS OF COMPANY NAME', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD, num_of_item=3),
                'id': _create_component_config('ID'),
                'name': _create_component_config('NAME', length=50),
                'type': _create_component_config('TYPE OF TRANSLATION'),
            },
            'nameRequest': {
                CommonConfigKeys.SECTION: _create_component_config('NAME OF COMPANY', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD),
                'address': {
                    CommonConfigKeys.ITEM: _create_component_config('ADDRESS'),
                    **common_address
                },
                'consent': _create_component_config('CONSENT'),
                'expires': _create_component_config('EXPIRES'),
                'legalName': _create_component_config('LEGAL NAME'),
                'legalType': _create_component_config('LEGAL TYPE'),
                'nrNumber': _create_component_config('NR NUMBER', length=10),
                'requestType': _create_component_config('TYPE OF NAME REQUEST'),
                'status': _create_component_config('STATUS'),
                'submittedBy': _create_component_config('SUBMITTED BY'),
            },
            'courtOrder':{
                CommonConfigKeys.SECTION: _create_component_config('COURT ORDER', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD),
                'effectOfOrder': _create_component_config('PLAN OF ARRANGEMENT', length=500),
                'fileKey': _create_component_config('THE IDENTIFIER FOR COURT ORDER FILE IN FILE SERVER'),
                'fileNumber': _create_component_config('ASSIGNED FILE NUMBER', length=20),
                'orderDate': _create_component_config('DATE AND TIME OF THE COURT ORDER'),
                'orderDetails': _create_component_config('PURPOSE OF THE COURT ORDER', length=2000),
            },
            'courtApproval': {
                CommonConfigKeys.SECTION: _create_component_config('With Court Approval', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD)
            },
            'contactPoint': {
                CommonConfigKeys.SECTION: _create_component_config('CONTACT POINT', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD),
                'email': _create_component_config('EMAIL'),
                'extension': _create_component_config('EXTENSION'),
                'phone': _create_component_config('PHONE NUMBER'),
            },
            'amalgamatingBusinesses': {
                CommonConfigKeys.SECTION: _create_component_config('AMALGAMATING CORPORATIONS', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD, num_of_item=5),
                'foreignJurisdiction': {
                    CommonConfigKeys.ITEM: _create_component_config('FOREIGN JURISDICTION'),
                    'country': _create_component_config('COUNTRY'),
                    'region': _create_component_config('PROVINCE/STATE'),
                },                
                'identifier': _create_component_config('IDENTIFIER'),
                'legalName':  _create_component_config('LEGAL NAME'),
                'role': _create_component_config('ROLE'),
            },
            'shareStructure': {
                CommonConfigKeys.SECTION: _create_component_config('AUTHORIZED SHARE STRUCTURE', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD),
                'resolutionDates': {
                    CommonConfigKeys.ITEM: _create_component_config('RESOLUTION DATE', num_of_item=5),
                },
                'shareClasses': {
                    CommonConfigKeys.ITEM: _create_component_config('SHARE CLASS', num_of_item=5),
                    'currency': _create_component_config('CURRENCY'),
                    'hasMaximumShares': _create_component_config('HAS MAXIMUM NUMBER OF SHARES'),
                    'hasParValue': _create_component_config('HAS INITIAL VALUE OF EACH SHARE'),
                    'hasRightsOrRestrictions': _create_component_config('HAS SPECIAL RIGHTS OR RESTRICTIONS'),
                    'maxNumberOfShares': _create_component_config('MAXIMUM NUMBER OF SHARES IN THE CLASS'),
                    'name': _create_component_config('THE NAME OF THE SHARE CLASS'),
                    'parValue': _create_component_config('INITIAL VALUE OF EACH SHARE'),
                    'priority': _create_component_config('ORDER OF THE SHARES'),
                    'series': {
                        CommonConfigKeys.ITEM: _create_component_config('SERIES', num_of_item=1),
                        'hasMaximumShares': _create_component_config('HAS MAXIMUM NUMBER OF SHARES'),
                        'hasRightsOrRestrictions': _create_component_config('HAS SPECIAL RIGHTS OR RESTRICTIONS'),
                        'maxNumberOfShares': _create_component_config('MAXIMUM NUMBER OF SHARES IN THE CLASS'),
                        'name': _create_component_config('THE NAME OF THE SHARE CLASS'),
                        'priority': _create_component_config('ORDER OF THE SHARES'),
                    },
                }, 
            },
            'offices':{
                CommonConfigKeys.SECTION: _create_component_config('OFFICES', font_size=PdfFontSize.SECTION_TITLE, font_style=PdfFontStyle.BOLD),
                'recordsOffice': {
                    CommonConfigKeys.ITEM: _create_component_config('RECORDS OFFICE'),
                    'deliveryAddress': common_deliveryAddress,
                    'mailingAddress': common_mailingAddress,
                    'officeType': _create_component_config('OFFICE TYPE')
                },
                'registeredOffice': {
                    CommonConfigKeys.ITEM: _create_component_config('REGISTERED OFFICE'),
                    'deliveryAddress': common_deliveryAddress,
                    'mailingAddress': common_mailingAddress,
                    'officeType': _create_component_config('OFFICE TYPE')
                },
            }
        }
    }
}
