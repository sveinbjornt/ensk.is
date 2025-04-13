#!/usr/bin/env python3
"""

Ensk.is - Free and open English-Icelandic dictionary

Copyright (c) 2021-2025, Sveinbjorn Thordarson <sveinbjorn@sveinbjorn.org>
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or other
materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may
be used to endorse or promote products derived from this software without specific
prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.


Generate a PDF version of the dictionary.


"""

import re
import string
from collections import OrderedDict

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    NextPageTemplate,
    PageBreak,
    FrameBreak,
    Flowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from info import PROJECT

_FONT_NAME = "Garamond"

# Global dictionary to track which letter appears on which pages
_LETTER_PAGES = OrderedDict()


def _add_page_number(canvas: Canvas, doc: BaseDocTemplate):
    """Custom page number function for drawing page numbers and headers on each page."""
    # Get current page number
    page_num = canvas.getPageNumber()
    
    # Don't add page number to the first page (cover)
    if page_num > 1:
        canvas.saveState()
        canvas.setFont(_FONT_NAME, 11)
        
        # Center the page number at the bottom
        canvas.drawCentredString(A4[0] / 2, 1 * cm, str(page_num - 1))  # Adjust for cover page
        
        # Add letter header at the top
        # Find which letter section this page belongs to
        current_letter = None
        for letter, (start_page, end_page) in _LETTER_PAGES.items():
            if start_page <= page_num <= end_page:
                current_letter = letter
                break
                
        if current_letter:
            canvas.setFont(f"{_FONT_NAME}-Bold", 14)
            canvas.drawCentredString(A4[0] / 2, A4[1] - 1 * cm, current_letter)
            
        canvas.restoreState()


def _load_fonts():
    """Load custom fonts for the PDF."""
    pdfmetrics.registerFont(TTFont(_FONT_NAME, f"fonts/{_FONT_NAME}.ttf"))
    pdfmetrics.registerFont(
        TTFont(f"{_FONT_NAME}-Bold", f"fonts/{_FONT_NAME}-Bold.ttf")
    )
    pdfmetrics.registerFont(
        TTFont(f"{_FONT_NAME}-Italic", f"fonts/{_FONT_NAME}-Italic.ttf")
    )


_ENTRY_LINK_REGEX = re.compile(r"%\[(.+?)\]%")


def _apply_styles(entry: str, definition: str) -> tuple[str, str]:
    """Apply custom styles to text."""
    ent = entry.replace("'", "’")
    e = f'<font face="{_FONT_NAME}-Bold">{ent}</font>'
    d = definition
    # Italicize links and English words
    d = _ENTRY_LINK_REGEX.sub(rf'<font face="{_FONT_NAME}-Italic">\1</font>', d)
    d = d.replace("[", f'<font face="{_FONT_NAME}-Italic">')
    d = d.replace("]", "</font>")
    d = d.replace("~", entry)
    d = d.replace("'", "’")
    return e, d


class LetterSectionMarker(Flowable):
    """A custom flowable to mark the start of a letter section and track page numbers."""
    
    def __init__(self, letter):
        Flowable.__init__(self)
        self.letter = letter
        self.width = 0
        self.height = 0
        
    def wrap(self, availWidth, availHeight):
        # Zero-sized flowable
        return (0, 0)
        
    def draw(self):
        # Save the page number for this letter section
        global _LETTER_PAGES
        page_num = self.canv.getPageNumber()  # Current page number from the canvas
        _LETTER_PAGES[self.letter] = [page_num, 999]  # Set end page to a high number initially
        
        # Update previous letter's end page if there is one
        prev_letter = None
        for l in _LETTER_PAGES.keys():
            if l == self.letter:
                break
            prev_letter = l
            
        if prev_letter:
            start_page, _ = _LETTER_PAGES[prev_letter]
            _LETTER_PAGES[prev_letter] = [start_page, page_num - 1]


def generate_pdf(dictionary_data, output_file):
    """Generate a PDF version of the dictionary."""
    _load_fonts()
    
    # Clear the global letter-page mapping
    global _LETTER_PAGES
    _LETTER_PAGES.clear()

    columns = 3

    # Set up document
    page_width, page_height = A4
    margin = 2 * cm

    # Calculate column layout
    col_width = (page_width - 2 * margin - (columns - 1) * 0.5 * cm) / columns
    col_height = page_height - 2 * margin

    # Create frames for each column (one frame per column)
    frames = []
    for i in range(columns):
        x = margin + i * (col_width + 0.5 * cm)
        frame = Frame(
            x,
            margin,
            col_width,
            col_height,
            leftPadding=0,
            bottomPadding=0,
            rightPadding=0,
            topPadding=0,
            id=f"col{i}",
        )
        frames.append(frame)

    # Create document template with frames
    doc = BaseDocTemplate(
        output_file,
        pagesize=A4,
        title=PROJECT.DICT_NAME,
        author=PROJECT.DICT_AUTHORS,
        subject=PROJECT.DESCRIPTION,
        keywords=PROJECT.DICT_KEYWORDS,
        creator=PROJECT.EDITOR,
        producer=PROJECT.NAME,
    )

    # Create a single frame for the cover page
    cover_frame = Frame(
        margin, margin, page_width - 2 * margin, page_height - 2 * margin, id="cover"
    )
    cover_template = PageTemplate(id="cover", frames=[cover_frame])

    # Template for the dictionary content with multiple columns
    content_template = PageTemplate(
        id="columns",
        frames=frames,
        onPage=_add_page_number,  # Add the page number function
    )

    # Add both templates
    doc.addPageTemplates([cover_template, content_template])

    # Define styles
    styles = getSampleStyleSheet()

    # Cover page title style
    cover_title_style = ParagraphStyle(
        "coverTitle",
        parent=styles["Heading1"],
        fontSize=24,
        alignment=1,  # Center
        spaceAfter=20,
        fontName=f"{_FONT_NAME}-Bold",
    )

    # Cover page subtitle style
    cover_subtitle_style = ParagraphStyle(
        "coverSubtitle",
        parent=styles["Heading2"],
        fontSize=16,
        alignment=1,  # Center
        spaceAfter=40,
        fontName=f"{_FONT_NAME}",
    )

    # Section style for letters
    section_style = ParagraphStyle(
        "section",
        parent=styles["Heading2"],
        fontSize=18,
        spaceBefore=10,
        spaceAfter=5,
        fontName=f"{_FONT_NAME}-Bold",
    )

    # Entry style
    entry_style = ParagraphStyle(
        "entry",
        parent=styles["Normal"],
        leading=12,  # Tighter line spacing
        spaceBefore=4,
        spaceAfter=0,
        firstLineIndent=-0.2 * cm,  # Hanging indent
        leftIndent=0 * cm,
        fontName=f"{_FONT_NAME}",
        fontSize=12,
        # justifyLastLine=True,
    )

    # Create content
    content = []

    # Add cover page content
    content.append(Spacer(1, 5 * cm))
    content.append(Paragraph("Ensk-íslensk orðabók", cover_title_style))
    content.append(Spacer(1, 1 * cm))
    content.append(
        Paragraph("eftir Geir T. Zoega og Sveinbjörn Þórðarson", cover_subtitle_style)
    )

    # Add page break and switch to columns template for main content
    content.append(NextPageTemplate("columns"))
    content.append(PageBreak())

    # Group entries by first letter
    grouped_entries = {}
    for english, icelandic in dictionary_data.items():
        first_letter = english[0].upper()
        if first_letter not in grouped_entries:
            grouped_entries[first_letter] = []
        grouped_entries[first_letter].append((english, icelandic))

    # Process each letter
    for letter in string.ascii_uppercase:
        if letter in grouped_entries:
            # Mark the start of this letter section
            content.append(LetterSectionMarker(letter))
            
            # Add letter header
            content.append(Paragraph(letter, section_style))
            
            # Add entries
            for english, icelandic in grouped_entries[letter]:
                # Format like a real dictionary: bold headword followed by definition
                w, d = _apply_styles(english, icelandic)
                entry_text = f"{w} {d}"
                content.append(Paragraph(entry_text, entry_style))

    # Generate the document - this will track all letter pages
    doc.build(content)
    
    # Set the end page for the last letter
    if _LETTER_PAGES:
        last_letter = list(_LETTER_PAGES.keys())[-1]
        start_page, _ = _LETTER_PAGES[last_letter]
        # Get the total page count from document
        total_pages = doc.canv.getPageNumber()
        _LETTER_PAGES[last_letter] = [start_page, total_pages]


if __name__ == "__main__":
    # Test PDF generation
    data = {}
    generate_pdf(data, "dictionary.pdf")
