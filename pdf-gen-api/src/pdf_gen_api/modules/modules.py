""" 
    Common modules for PDF Rendering
"""

from typing import List
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black
from reportlab.pdfbase.pdfmetrics import stringWidth
import os, random, re
from pdf_gen_api.resources import (
    PdfFontSize, PdfFontStyle, FieldSize, 
    MAIN_TITLE_Y, TITLE_X, UNIT_WIDTH, START_Y, MARGIN_BOTTOM
)


# modularized header section
def add_header(canvas: canvas.Canvas, title: str) -> int:
    """The Header PDF Module

    Args:
        canvas (canvas.Canvas): The PDF canvas the generator is using
        title (str): The title of the PDF
        fee (float): The calculated fee for this filing
    Returns:
        int: the last edit y axis value after adding this module
    """
    current_y = 720
    # top-left logo
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    logo_relative_path = os.path.join('res', 'logo.png')
    logo_path = os.path.join(project_root, logo_relative_path)
    canvas.drawImage(logo_path, 20, current_y, 180, 60)
    current_y -= 5
    # top-right form title
    canvas.setFont(PdfFontStyle.REGULAR.value , PdfFontSize.FILE_TITLE.value) 
    canvas.drawRightString(597, MAIN_TITLE_Y, title)
    # 1st divider
    canvas.line(15, current_y, 597, current_y)
    current_y -= 10
    # contact info 1st row
    canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.TITLE_CONTACT_INFO.value)
    canvas.drawString(15, current_y, 'Telephone: 1 877 526 - 1526')
    canvas.drawString(UNIT_WIDTH, current_y, 'Mailing Address:  PO Vox 9431 Stn Prov Govt')
    canvas.drawString(UNIT_WIDTH * 2, current_y, 'Courier Address:  200-940 Blanshard Street')
    current_y -= 10
    # contact info 2nd row
    canvas.setFont(PdfFontStyle.BOLD.value, PdfFontSize.TITLE_CONTACT_INFO.value)
    canvas.drawString(15, current_y, 'Email: bcregistries@gov.bc.ca')
    canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.TITLE_CONTACT_INFO.value)
    canvas.drawString(UNIT_WIDTH + 65, current_y, 'Victoria BC V8W 9V3')
    canvas.drawString(UNIT_WIDTH * 2 + 65, current_y, 'Victoria BC V8W 3E6')
    current_y -= 6
    # 2nd divider
    canvas.line(15, current_y, 597, current_y)
    current_y -= 8
    return current_y



# modularized certification section
def add_certification_section(canvas: canvas.Canvas, start_y: int, num_of_items: int, config: dict) -> int:
    """Certification PDF Module
    Args:
        canvas (canvas.Canvas): The PDF canvas the generator is using
        start_y (int): the last edit y axis value
        width (int): the width of the content area
        num_of_items (int): number of certification rows to generate
        config (dict): configuration parameters including certification info
    
    Return:
        int: the last edit y axis value after adding this module
    """
    current_y = start_y
    line_height = 25
    entry_height = 45  # increased to adjust field headers

    fields = config.get('fields', ['NAME', 'SIGNATURE', 'DATE'])
    date_format = config.get('date_format', 'YYYY/MM/DD')
    page_width, _ = letter

    def draw_field_headers(y):
        canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.CONTENT.value)
        for i, field in enumerate(fields):
            canvas.drawString(TITLE_X + FieldSize.SMALL.value * i, y + 5, field)
        canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.SMALL_NOTE.value)
        canvas.drawString((FieldSize.MID.value + 45), y + 5, date_format)
        return y - 25

    def add_certification_entry(y, line_num):
        y = draw_field_headers(y)
        form = canvas.acroForm
        for i in range(len(fields)):
            form.textfield(
                name = f'certification_{line_num}_{i}',
                x = TITLE_X + FieldSize.SMALL.value * i,
                y = y,
                width = FieldSize.SMALL.value,
                height = 20,
                borderWidth = 0.5,
                borderStyle = 'solid',
            )
        return y - line_height

    def draw_section_header():
        nonlocal current_y
        current_y -= 20
        canvas.line(TITLE_X, current_y, page_width - TITLE_X, current_y)
        current_y -= 12

        # Section Title & description
        canvas.setFont(PdfFontStyle.BOLD.value, PdfFontSize.SECTION_TITLE.value)
        canvas.drawString(TITLE_X, current_y, config.get('title', 'CERTIFICATION'))
        current_y -= 20
        canvas.setFont(PdfFontStyle.ITALIC.value, PdfFontSize.CONTENT.value)
        description = config.get('description', '')
        if len(description) > 0:
            canvas.drawString(TITLE_X, current_y, f'{description}')
            current_y -= 15

        # Section Note
        canvas.setFont(PdfFontStyle.BOLD.value, PdfFontSize.SMALL_NOTE.value)
        note = config.get('note', '')
        canvas.drawString(TITLE_X, current_y, note)
        current_y -= 20

    show_header = True
    if show_header:
        draw_section_header()

    for item_index in range(num_of_items):
        if current_y < 75 + entry_height:  # check if we have enough space for the entire entry
            canvas.showPage()
            current_y = START_Y  # reset to top of new page

        current_y = add_certification_entry(current_y, item_index)

    return current_y



def add_top_notes(canvas: canvas.Canvas, start_y: int, top_note_info:dict, fee:float=0.0, ) -> int:
    line_gap = 10
    beginning_y = start_y - 8
    current_y = beginning_y - 16

    # the left section (paragraph only)
    canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.BOLD_NOTE.value)
    left_paragraph = top_note_info['left_column']
    for line in left_paragraph:
        canvas.drawString(TITLE_X, current_y, line)
        current_y -= line_gap
    left_end_y = current_y

    # the right section (paragraph + rectangle)
    right_paragraph = top_note_info['right_column']
    def find_longest_line_length() -> int:
        maxLen = 0
        for line in right_paragraph:
            maxLen = max(maxLen, len(line))
        return maxLen
    longest_line = find_longest_line_length()
    rectangle_width = longest_line/70 * 300
    current_y = beginning_y - 12
    right_section_x_adjustment = 600 - longest_line * 4.45
    
    
    for line in right_paragraph:
        canvas.drawString(TITLE_X + right_section_x_adjustment, current_y, line)
        current_y -= line_gap
    # right side rectangle
    current_y -= 8
    canvas.rect(TITLE_X + right_section_x_adjustment - 8, current_y+10, rectangle_width, (beginning_y-current_y-8), stroke=1, fill=0)
    right_end_y = current_y

    # bottom divider
    divider_y = min(left_end_y, right_end_y)
    divider_y -= line_gap
    canvas.line(TITLE_X, divider_y, 597, divider_y)

    return divider_y



# modularized footer section
def add_footer(canvas: canvas.Canvas, form_info: str, page_number: int) -> None:
    """The Footer PDF Module

    Args:
        canvas (canvas.Canvas): The PDF canvas the generator is using
        form_info (str): Information about the form (e.g., form number and date)
        page_number (int): Current page number
    """
    footer_y = 20

    # Add a line above the footer
    canvas.line(15, footer_y + 15, 597, footer_y + 15)

    # Add form info on the left side
    canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.SMALL_NOTE.value)
    canvas.drawString(15, footer_y, form_info)

    # Add page number on the right side
    canvas.drawRightString(597, footer_y, f"Page {page_number}")



# modularized effective date section
def add_effective_date_section(canvas: canvas.Canvas, start_y: int, filing_name: str) -> int:
    """Effective Date PDF Module

    Args:
        canvas (canvas.Canvas): The PDF canvas the generator is using
        start_y (int): the last edit y axis value
        filing_name (str): The name of the filing (e.g., "amalgamation")

    Returns:
        int: the last edit y axis value after adding this module
    """
    current_y = start_y - 20
    line_height = 20
    radio_size = 17
    date_field_width = 100
    time_field_width = 50

    # Generate a unique identifier for this section
    section_id = str(random.random())

    # Title
    canvas.setFont(PdfFontStyle.BOLD.value, PdfFontSize.CONTENT.value)
    canvas.drawString(TITLE_X, current_y, f"{filing_name.upper()} EFFECTIVE DATE")
    current_y -= line_height * 1.5

    # Create a radio button group for the three options
    group_name = f"effective_date_option_{section_id}"

    # Option 1
    canvas.acroForm.radio(
        name=group_name,
        value="option1",
        x=TITLE_X,
        y=current_y,
        size=radio_size,
    )
    canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.CONTENT.value)
    canvas.drawString(TITLE_X + radio_size + 5, current_y + 3, f"The {filing_name} is to take effect at the time that this is filed with the registrar.")
    current_y -= line_height * 1.5

    # Option 2
    canvas.acroForm.radio(
        name=group_name,
        value="option2",
        x=TITLE_X,
        y=current_y,
        size=radio_size,
    )
    option2_text = f"The {filing_name} is to take effect at 12:01a.m. Pacific Time on"
    canvas.drawString(TITLE_X + radio_size + 5, current_y + 3, option2_text)

    option2_text_width = canvas.stringWidth(option2_text, PdfFontStyle.REGULAR.value, PdfFontSize.CONTENT.value)

    # Add YYYY / MM / DD above the textfield
    canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.SMALL_NOTE.value)
    canvas.drawString(TITLE_X + radio_size + 5 + option2_text_width + 5, current_y + line_height, "YYYY / MM / DD")

    canvas.acroForm.textfield(
        name=f'effective_date_option2_date_{section_id}',
        x=TITLE_X + radio_size + 5 + option2_text_width + 5,
        y=current_y - 2,
        width=date_field_width,
        height=20,
        borderStyle='underlined',
        maxlen=10
    )
    canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.CONTENT.value)
    canvas.drawString(TITLE_X + radio_size + 5, current_y - line_height, f"being a date that is not more than ten days after the date of the filing.")
    current_y -= line_height * 2.5

    # Option 3
    canvas.acroForm.radio(
        name=group_name,
        value="option3",
        x=TITLE_X,
        y=current_y,
        size=radio_size,
    )
    canvas.drawString(TITLE_X + radio_size + 5, current_y + 3, f"The {filing_name} is to take effect at")

    # Time field
    time_field_x = TITLE_X + UNIT_WIDTH
    canvas.acroForm.textfield(
        name=f'effective_date_option3_time_{section_id}',
        x=time_field_x,
        y=current_y - 2,
        width=time_field_width,
        height=20,
        borderStyle='underlined',
        maxlen=5
    )

    # Add A.M./P.M. radio buttons
    ampm_group_name = f'effective_date_option3_ampm_{section_id}'
    am_pm_x = time_field_x + time_field_width + 10

    canvas.acroForm.radio(
        name=ampm_group_name,
        value='AM',
        x=am_pm_x,
        y=current_y,
        size=radio_size,
        buttonStyle='check'
    )
    canvas.drawString(am_pm_x + radio_size + 2, current_y + 3, "a.m.")

    canvas.acroForm.radio(
        name=ampm_group_name,
        value='PM',
        x=am_pm_x + 50,
        y=current_y,
        size=radio_size,
        buttonStyle='check'
    )
    canvas.drawString(am_pm_x + 50 + radio_size + 2, current_y + 3, "p.m.")

    pacific_time_x = am_pm_x + 100
    canvas.drawString(pacific_time_x, current_y + 3, "Pacific Time on")

    total_width_before_pacific = pacific_time_x - TITLE_X + canvas.stringWidth("Pacific Time on", PdfFontStyle.REGULAR.value, PdfFontSize.CONTENT.value)

    date_x = TITLE_X + total_width_before_pacific + 5
    canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.SMALL_NOTE.value)
    canvas.drawString(date_x, current_y + line_height, "YYYY / MM / DD")

    canvas.acroForm.textfield(
        name=f'effective_date_option3_date_{section_id}',
        x=date_x,
        y=current_y - 2,
        width=date_field_width,
        height=20,
        borderStyle='underlined',
        maxlen=10
    )

    canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.CONTENT.value)
    canvas.drawString(TITLE_X + radio_size + 5, current_y - line_height, f"being a date and time that is not more than ten days after the date of the filing.")
    current_y -= line_height * 2

    return current_y



def add_radios_group(pdf_canvas:canvas.Canvas, start_y:int, content_list:list, font_style:PdfFontStyle, font_size:PdfFontSize) -> int:
        """ DO NOT directly invoke this method, invoke create_from_enum_obj in the Generator instead
            Helper method - to add radios group component
        """
        pdf_canvas.setFont(font_style.value, font_size.value)
        current_y = start_y - 10

        # create radio button group
        for option in content_list:
            # Create a radio button
            pdf_canvas.acroForm.radio(
                name="name",
                value=option+str(random.random()),
                selected=False,
                x=TITLE_X,
                y=current_y,
                size=20,
                borderStyle='solid',
                borderColor=black,
                borderWidth=0.5,
                forceBorder=True          
            )
            # Add Labels on the right-hand side of the radio buttons
            pdf_canvas.drawString(TITLE_X + 25, current_y + 5, option)
            current_y -= 25  # margin between options
        return current_y



def add_dropdown_menu(pdf_canvas:canvas.Canvas, start_y:int, content_list:list, font_style:PdfFontStyle, font_size:PdfFontSize) -> int:
        """ DO NOT directly invoke this method, invoke create_from_enum_obj in the Generator instead
            Helper method - to add a dropdown component
        """
        pdf_canvas.setFont(font_style.value, font_size.value)
        current_y = start_y - 5
        # Create the dropdown menu
        pdf_canvas.acroForm.choice(
            options=content_list,
            value=' ',
            x=TITLE_X,
            y=current_y,
            width=200,
            height=20,
        )
        current_y -= 15 # margin after the dropdown
        return current_y



def add_textfield(pdf_canvas:canvas.Canvas, start_y:int, font_style:PdfFontStyle, font_size:PdfFontSize, length:int) -> int:
    """Add a textfield component"""
    pdf_canvas.setFont(font_style.value, font_size.value)
    current_y = start_y + 15

    size, lines, field_flag = _calculate_field_properties(length)
    #current_y -= 20 * lines + 2
    pdf_canvas.acroForm.textfield(
        name="textfield" + str(random.random()),
        x=TITLE_X,
        y=current_y,
        width=size,
        height=20 * lines,
        borderWidth=0.5,
        borderStyle='underlined',
        fieldFlags=field_flag,
        maxlen=length
    )
    current_y -= 10
    return current_y


def _calculate_field_properties(length):
    """Calculate the width of a field based on its length."""
    if length < 30:
        size = FieldSize.SMALL.value
        lines = 1
    elif length < 60:
        size = FieldSize.MID.value
        lines = 1
    else:
        size = FieldSize.LARGE.value
        lines = max(1, length // 400)

    field_flag = 'multiline' if lines > 1 else ''
    return size, lines, field_flag



def add_single_checkbox(pdf_canvas:canvas.Canvas, start_y:int, title:str, font_style:PdfFontStyle, font_size:PdfFontSize) -> int:
    """Add a checkbox component"""
    pdf_canvas.setFont(font_style.value, font_size.value)
    current_y = start_y - 25
    # create a checkbox
    pdf_canvas.acroForm.checkbox(
        name="checkbox" + str(random.random()),
        x=TITLE_X,
        y = current_y,
        size=20,
        checked=False
    )
    current_y += 5
    # add text next to the checkbox
    pdf_canvas.drawString(TITLE_X+30, current_y, title)
    current_y -= 15
    return current_y


def add_instruction_section(pdf_canvas: canvas.Canvas, start_y: int, instructions: dict, filing_name: str) -> int:
    """Add the instruction module to the PDF with improved formatting.

    Args:
        pdf_canvas (canvas.Canvas): The PDF canvas the generator is using.
        start_y (int): The starting y-coordinate for the instruction section.
        instructions (dict): A dictionary containing instruction data.
        filing_name (str): The name of the filing (e.g., "amalgamation_application").

    Returns:
        int: The updated y-coordinate after adding the instruction section.
    """
    current_y = start_y - 30
    page_width, _ = letter
    page_height = 792

    # Formatted instructions title
    formatted_title = filing_name.replace('_', ' ').upper() + " INSTRUCTIONS"
    pdf_canvas.setFont(PdfFontStyle.BOLD.value, PdfFontSize.SECTION_TITLE.value)
    title_width = stringWidth(formatted_title, PdfFontStyle.BOLD.value, PdfFontSize.SECTION_TITLE.value)
    pdf_canvas.drawString((page_width - title_width) / 2, current_y, formatted_title)
    current_y -= 30

    for key, value in instructions.items():
        description = value.get('description', '')
        examples = value.get('examples', [])

        # Check if we need to start a new page
        if current_y < MARGIN_BOTTOM:
            pdf_canvas.showPage()
            current_y = page_height - 20

        # Formatted field name
        formatted_key = _format_key(key)
        pdf_canvas.setFont(PdfFontStyle.BOLD.value, PdfFontSize.CONTENT.value)
        pdf_canvas.drawString(TITLE_X, current_y, formatted_key)
        current_y -= 20

        pdf_canvas.setFont(PdfFontStyle.REGULAR.value, PdfFontSize.CONTENT.value)
        lines = _split_text(pdf_canvas, description, page_width - 2 * TITLE_X)
        for line in lines:
            if current_y < MARGIN_BOTTOM:
                pdf_canvas.showPage()
                current_y = page_height - 20
            pdf_canvas.drawString(TITLE_X, current_y, line)
            current_y -= 15

        if examples:
            current_y -= 5
            if current_y < MARGIN_BOTTOM:
                pdf_canvas.showPage()
                current_y = page_height - 20
            pdf_canvas.drawString(TITLE_X, current_y, "Examples:")
            current_y -= 15
            for example in examples:
                if current_y < MARGIN_BOTTOM:
                    pdf_canvas.showPage()
                    current_y = page_height - 20
                pdf_canvas.drawString(TITLE_X + 10, current_y, f"- {example}")
                current_y -= 15

        current_y -= 10

    return current_y

def _format_key(key: str) -> str:
    """Format the key to expected output.

    Args:
        key (str): The original key string to be formatted.

    Returns:
        str: The formatted key string with each word capitalized and separated by spaces.
    """
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+', key)
    words = [word.capitalize() for word in words]
    return ' '.join(words)


def _split_text(pdf_canvas: canvas.Canvas, text: str, max_width: int) -> List[str]:
    """Split text into lines that fit within max_width.

    Args:
        pdf_canvas (canvas.Canvas): The PDF canvas used for width calculations.
        text (str): The text to be split.
        max_width (int): The maximum width allowed for each line.

    Returns:
        List[str]: A list of strings, each representing a line of text that fits within max_width.
    """
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        if stringWidth(' '.join(current_line + [word]), PdfFontStyle.REGULAR.value, PdfFontSize.CONTENT.value) < max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines
