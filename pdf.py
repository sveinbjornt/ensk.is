from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, FrameBreak, NextPageTemplate, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import string
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def create_dictionary_pdf(dictionary_data, output_file, columns=2):

    pdfmetrics.registerFont(TTFont("EBGaramond", "fonts/EBGaramond.ttf"))
    pdfmetrics.registerFont(TTFont("EBGaramond-Bold", "fonts/EBGaramond-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("EBGaramond-Italic", "fonts/EBGaramond-Italic.ttf"))

    # Set up document
    page_width, page_height = A4
    margin = 2 * cm

    # Calculate column layout
    col_width = (page_width - 2*margin - (columns-1)*0.5*cm) / columns
    col_height = page_height - 2*margin

    # Create frames for each column (one frame per column)
    frames = []
    for i in range(columns):
        x = margin + i * (col_width + 0.5*cm)
        frame = Frame(x, margin, col_width, col_height, leftPadding=0, bottomPadding=0, 
                      rightPadding=0, topPadding=0, id=f'col{i}')
        frames.append(frame)

    # Create document template with frames
    doc = BaseDocTemplate(output_file, pagesize=A4)
    
    # Create a single frame for the cover page
    cover_frame = Frame(margin, margin, page_width-2*margin, page_height-2*margin, id='cover')
    cover_template = PageTemplate(id='cover', frames=[cover_frame])
    
    # Template for the dictionary content with multiple columns
    content_template = PageTemplate(id='columns', frames=frames)
    
    # Add both templates
    doc.addPageTemplates([cover_template, content_template])

    # Define styles
    styles = getSampleStyleSheet()

    # Cover page title style
    cover_title_style = ParagraphStyle(
        'coverTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=1,  # Center
        spaceAfter=20,
        fontName="EBGaramond-Bold",
    )
    
    # Cover page subtitle style
    cover_subtitle_style = ParagraphStyle(
        'coverSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        alignment=1,  # Center
        spaceAfter=40,
        fontName="EBGaramond",
    )

    # Section style for letters
    section_style = ParagraphStyle(
        'section',
        parent=styles['Heading2'],
        fontSize=18,
        spaceBefore=10,
        spaceAfter=5,
        fontName="EBGaramond-Bold",
    )

    # Entry style
    entry_style = ParagraphStyle(
        'entry',
        parent=styles['Normal'],
        leading=12,  # Tighter line spacing
        spaceBefore=4,
        spaceAfter=0,
        firstLineIndent=-0.2*cm,  # Hanging indent
        leftIndent=0*cm,
        fontName="EBGaramond",
        fontSize=12,
        justifyLastLine=True,

    )

    # Create content
    content = []

    # Add cover page content
    content.append(Paragraph("Ensk-íslensk orðabók", cover_title_style))
    content.append(Spacer(1, 1*cm))
    content.append(Paragraph("eftir Geir T. Zoega og Sveinbjörn Þórðarson", cover_subtitle_style))
    
    # Add page break and switch to columns template for main content
    content.append(NextPageTemplate('columns'))
    content.append(PageBreak())
    
    # Group entries by first letter
    grouped_entries = {}
    for english, icelandic in dictionary_data.items():
        first_letter = english[0].upper()
        if first_letter not in grouped_entries:
            grouped_entries[first_letter] = []
        grouped_entries[first_letter].append((english, icelandic))

    import re
    rx = re.compile(r"%\[(.+?)\]%")


    # Process each letter
    for letter in string.ascii_uppercase:
        if letter in grouped_entries:
            # Add letter header
            content.append(Paragraph(letter, section_style))
            # Add entries
            for english, icelandic in grouped_entries[letter]:
                # Format like a real dictionary: bold headword followed by definition
                x = icelandic
                # Italicize English words
                x = rx.sub(rf'<font face="EBGaramond-Italic">\1</font>', x)
                x = x.replace("[", '<font face="EBGaramond-Italic">')
                x = x.replace("]", '</font>')
                x = x.replace("~", english)

                entry_text = f'<font face="EBGaramond-Bold">{english}</font> {x}'
                content.append(Paragraph(entry_text, entry_style))

    # Build document
    doc.build(content)
