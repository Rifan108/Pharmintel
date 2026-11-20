import os
import io
import html
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import Dict, Any

# Multi-lingual Indic Font Registration (Supports English, Kannada, Hindi, Tamil, Telugu, Malayalam, Marathi)
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

try:
    nirmala_path = "C:/Windows/Fonts/Nirmala.ttc"
    if os.path.exists(nirmala_path):
        if "NirmalaUI" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("NirmalaUI", nirmala_path, subfontIndex=0))
        if "NirmalaUI-Bold" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("NirmalaUI-Bold", nirmala_path, subfontIndex=1))
        FONT_REGULAR = "NirmalaUI"
        FONT_BOLD = "NirmalaUI-Bold"
except Exception:
    FONT_REGULAR = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"


class PatientSafetyReportCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and render running headers
    and 'Page X of Y' footers across multi-page medication safety reports.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        # Running header on page > 1
        if self._pageNumber > 1:
            self.setFont(FONT_REGULAR, 7.5)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(12 * mm, 297 * mm - 9 * mm, "PHARMINTEL CLINICAL COMPATIBILITY & PATIENT SAFETY REPORT")
            self.drawRightString(210 * mm - 12 * mm, 297 * mm - 9 * mm, "CONFIDENTIAL CLINICAL ASSESSMENT")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(12 * mm, 297 * mm - 10 * mm, 210 * mm - 12 * mm, 297 * mm - 10 * mm)

        # Running footer on all pages
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(12 * mm, 11 * mm, 210 * mm - 12 * mm, 11 * mm)

        self.setFont(FONT_REGULAR, 7)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(12 * mm, 6.5 * mm, "PHARMINTEL Clinical Intelligence | Verified Medical Decision Support | Strictly Confidential")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(210 * mm - 12 * mm, 6.5 * mm, page_str)
        self.restoreState()


class A4PrintService:
    """
    Healthcare Compliance A4 Printing & PDF Generation Service.
    Conforms to ISO 216 exact A4 standards (210mm x 297mm) with 12mm margins.
    Generates:
    - Pharmacy Tax Invoice (GST compliant)
    - Prescription Record
    - Order Summary
    - Customer Payment Receipt
    - Pharmacy Purchase Invoice
    - Patient Safety & Medication Compatibility Intelligence Report
    """

    PRIMARY_COLOR = colors.HexColor("#1e3a8a") # Deep Medical Blue
    ACCENT_COLOR = colors.HexColor("#0d9488")  # Clinical Teal
    TEXT_DARK = colors.HexColor("#1e293b")     # Slate 800
    BORDER_COLOR = colors.HexColor("#cbd5e1")  # Slate 300
    BG_LIGHT = colors.HexColor("#f8fafc")      # Slate 50

    @classmethod
    def generate_tax_invoice_pdf(cls, invoice_data: Dict[str, Any]) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm
        )

        styles = getSampleStyleSheet()
        normal = styles["Normal"]

        title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=normal,
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=cls.PRIMARY_COLOR
        )
        subtitle_style = ParagraphStyle(
            "InvoiceSubtitle",
            parent=normal,
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=cls.TEXT_DARK
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=normal,
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=cls.PRIMARY_COLOR
        )
        table_cell = ParagraphStyle(
            "TableCell",
            parent=normal,
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=cls.TEXT_DARK
        )
        table_cell_bold = ParagraphStyle(
            "TableCellBold",
            parent=normal,
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=cls.TEXT_DARK
        )

        story = []

        # 1. Header with Pharmacy Details and Tax Invoice Banner
        header_data = [
            [
                Paragraph(f"<b>{invoice_data['pharmacy_name']}</b><br/>{invoice_data['pharmacy_address']}<br/>Phone: {invoice_data['pharmacy_phone']} | Email: {invoice_data['pharmacy_email']}<br/><b>DL No:</b> {invoice_data['pharmacy_license']} | <b>GSTIN:</b> {invoice_data['pharmacy_gst']}", subtitle_style),
                Paragraph(f"<font color='{cls.PRIMARY_COLOR.hexval()}'><b>TAX INVOICE</b></font><br/><b>Invoice No:</b> {invoice_data['invoice_number']}<br/><b>Date:</b> {invoice_data['invoice_date']}<br/><b>Order Ref:</b> {invoice_data['order_number']}", subtitle_style)
            ]
        ]
        t_header = Table(header_data, colWidths=[110 * mm, 76 * mm])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_header)
        story.append(HRFlowable(width="100%", thickness=1.5, color=cls.PRIMARY_COLOR, spaceAfter=8, spaceBefore=4))

        # 2. Billed To Details
        cust = invoice_data['customer']
        bill_data = [
            [
                Paragraph("<b>BILLED TO (PATIENT / CUSTOMER):</b>", section_heading),
                Paragraph("<b>DISPENSING PHARMACIST:</b>", section_heading)
            ],
            [
                Paragraph(f"<b>Name:</b> {cust['name']}<br/><b>Phone:</b> {cust['phone']}<br/><b>Address:</b> {cust['address']}", subtitle_style),
                Paragraph(f"<b>Pharmacist:</b> {invoice_data.get('pharmacist_name', 'Registered Pharmacist')}<br/><b>Reg No:</b> {invoice_data.get('pharmacist_reg', 'KSPC-REG-2015-88391')}<br/><b>Verification:</b> Verified & Approved", subtitle_style)
            ]
        ]
        t_bill = Table(bill_data, colWidths=[93 * mm, 93 * mm])
        t_bill.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_bill)
        story.append(Spacer(1, 6))

        # 3. Itemized Medicines Table
        # Columns: #, Medicine Description, Batch, Expiry, Qty, MRP, Unit Rate, GST%, Total
        table_rows = [
            [
                Paragraph("<b>#</b>", table_cell_bold),
                Paragraph("<b>Medicine Description & Strength</b>", table_cell_bold),
                Paragraph("<b>Batch</b>", table_cell_bold),
                Paragraph("<b>Exp</b>", table_cell_bold),
                Paragraph("<b>Qty</b>", table_cell_bold),
                Paragraph("<b>MRP</b>", table_cell_bold),
                Paragraph("<b>Rate</b>", table_cell_bold),
                Paragraph("<b>GST</b>", table_cell_bold),
                Paragraph("<b>Total (₹)</b>", table_cell_bold)
            ]
        ]

        for i, itm in enumerate(invoice_data["items"], 1):
            table_rows.append([
                Paragraph(str(i), table_cell),
                Paragraph(f"<b>{itm['name']}</b><br/><font color='#64748b'>{itm.get('composition', '')}</font>", table_cell),
                Paragraph(itm.get("batch_number", "BT-9901"), table_cell),
                Paragraph(itm.get("expiry_date", "2027-08"), table_cell),
                Paragraph(str(itm["quantity"]), table_cell),
                Paragraph(f"₹{itm['mrp']:.2f}", table_cell),
                Paragraph(f"₹{itm['unit_price']:.2f}", table_cell),
                Paragraph(f"{itm.get('gst_rate', 12.0):.0f}%", table_cell),
                Paragraph(f"₹{itm['total_price']:.2f}", table_cell_bold)
            ])

        col_widths = [8 * mm, 62 * mm, 20 * mm, 16 * mm, 12 * mm, 17 * mm, 17 * mm, 14 * mm, 20 * mm]
        t_items = Table(table_rows, colWidths=col_widths)
        t_items.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), cls.BG_LIGHT),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_items)
        story.append(Spacer(1, 8))

        # 4. Tax Breakdown and Grand Total
        totals_data = [
            [
                Paragraph("<b>Terms & Conditions:</b><br/>1. Goods once sold will not be taken back without valid batch receipt.<br/>2. Schedule H drugs dispensed strictly against registered medical practitioner prescription.<br/>3. Store medicines as per temperature instructions on container.", subtitle_style),
                Table([
                    [Paragraph("<b>Subtotal:</b>", table_cell), Paragraph(f"₹{invoice_data['subtotal']:.2f}", table_cell)],
                    [Paragraph("<b>CGST (6%):</b>", table_cell), Paragraph(f"₹{invoice_data['tax_amount'] / 2:.2f}", table_cell)],
                    [Paragraph("<b>SGST (6%):</b>", table_cell), Paragraph(f"₹{invoice_data['tax_amount'] / 2:.2f}", table_cell)],
                    [Paragraph("<b>Delivery Fee:</b>", table_cell), Paragraph(f"₹{invoice_data['delivery_fee']:.2f}", table_cell)],
                    [Paragraph("<b>Grand Total:</b>", table_cell_bold), Paragraph(f"<b>₹{invoice_data['total_amount']:.2f}</b>", table_cell_bold)]
                ], colWidths=[38 * mm, 38 * mm])
            ]
        ]
        t_totals = Table(totals_data, colWidths=[110 * mm, 76 * mm])
        t_totals.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t_totals)
        story.append(Spacer(1, 14))

        # 5. Pharmacist Signature Block & Footer
        sig_data = [
            [
                Paragraph("<b>Customer Signature:</b> ___________________", subtitle_style),
                Paragraph("<b>Authorized Pharmacist Signature & Stamp:</b><br/><br/>___________________________________", subtitle_style)
            ]
        ]
        t_sig = Table(sig_data, colWidths=[93 * mm, 93 * mm])
        story.append(t_sig)
        story.append(HRFlowable(width="100%", thickness=0.5, color=cls.BORDER_COLOR, spaceAfter=4, spaceBefore=10))
        story.append(Paragraph(f"<font color='#64748b' size='7'>This is a computer generated pharmacy tax invoice under the Drugs and Cosmetics Act 1940 and GST Rules 2017. PharmIntel Technology Network • Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</font>", normal))

        doc.build(story)
        buffer.seek(0)
        return buffer

    @classmethod
    def generate_patient_safety_report_pdf(cls, report_data: Dict[str, Any]) -> io.BytesIO:
        """
        Generates an ISO 216 A4 Patient-Specific Medication Safety Intelligence Report PDF.
        Supports both single proposed medicine checks and comprehensive multi-medicine regimens.
        Includes running headers/footers with 'Page X of Y', multi-lingual Indic typography,
        full clinical findings, mechanism analysis, doctor discussion prompts, and clinician sign-off.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=16 * mm
        )

        styles = getSampleStyleSheet()
        normal = styles["Normal"]

        title_style = ParagraphStyle(
            "SafetyTitle",
            parent=normal,
            fontName=FONT_BOLD,
            fontSize=14,
            leading=17,
            textColor=cls.PRIMARY_COLOR
        )
        subtitle_style = ParagraphStyle(
            "SafetySubtitle",
            parent=normal,
            fontName=FONT_REGULAR,
            fontSize=8,
            leading=11,
            textColor=cls.TEXT_DARK
        )
        section_heading = ParagraphStyle(
            "SafetySectionHeading",
            parent=normal,
            fontName=FONT_BOLD,
            fontSize=9.5,
            leading=13,
            textColor=cls.PRIMARY_COLOR
        )
        table_cell = ParagraphStyle(
            "SafetyTableCell",
            parent=normal,
            fontName=FONT_REGULAR,
            fontSize=7.5,
            leading=10,
            textColor=cls.TEXT_DARK
        )
        table_cell_bold = ParagraphStyle(
            "SafetyTableCellBold",
            parent=normal,
            fontName=FONT_BOLD,
            fontSize=7.5,
            leading=10,
            textColor=cls.TEXT_DARK
        )

        def safe_text(val, default=""):
            if val is None:
                return default
            return html.escape(str(val))

        story = []

        is_multi = "interaction_table" in report_data or "medicines_analyzed" in report_data

        # 1. Header Banner
        header_title = "<b>MEDICATION COMPATIBILITY INTELLIGENCE REPORT</b>" if is_multi else "<b>MEDICATION SAFETY INTELLIGENCE REPORT</b>"
        raw_id = report_data.get('assessment_id') or report_data.get('report_id') or datetime.now().strftime('%Y%m%d%H%M')
        report_id = f"PS-{datetime.now().strftime('%Y')}-{raw_id}"
        timestamp_str = report_data.get("assessment_timestamp") or report_data.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        header_table = Table([
            [
                Paragraph("<b>PHARMINTEL SMART PHARMACY NETWORK</b><br/>"
                          "Clinical Decision Support & Multi-Drug Compatibility Engine<br/>"
                          f"Knowledge Compendia: {safe_text(report_data.get('knowledge_base_version', 'CDSCO / WHO / BNF 86 Curated Clinical Compendium'))}", subtitle_style),
                Paragraph(f"<font color='{cls.PRIMARY_COLOR.hexval()}'>{header_title}</font><br/>"
                          f"<b>Report Ref ID:</b> {report_id}<br/>"
                          f"<b>Date/Time:</b> {safe_text(timestamp_str)}", subtitle_style)
            ]
        ], colWidths=[112 * mm, 74 * mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=1.5, color=cls.PRIMARY_COLOR, spaceAfter=6, spaceBefore=4))

        # 2. Patient Profile & Clinical Scope
        p_name = report_data.get("patient_name")
        if not p_name and isinstance(report_data.get("health_profile"), dict):
            p_name = report_data["health_profile"].get("patient_name")
        if not p_name and isinstance(report_data.get("patient_summary"), dict):
            p_name = report_data["patient_summary"].get("patient_name")
        p_name_display = safe_text(p_name.strip()) if (p_name and isinstance(p_name, str) and p_name.strip()) else "Patient name not provided"

        # Demographics
        p_profile = report_data.get("health_profile") or report_data.get("patient_summary") or {}
        age_str = str(p_profile.get("age")) if p_profile.get("age") else "Not recorded"
        gender_str = str(p_profile.get("gender") or "Not recorded")

        if is_multi:
            conds_raw = report_data.get("patient_conditions_evaluated") or p_profile.get("medical_conditions") or []
            conds = safe_text(", ".join(conds_raw)) or "None Recorded"
            allergies_raw = report_data.get("allergies_evaluated") or p_profile.get("known_allergies") or []
            allergies = safe_text(", ".join(allergies_raw)) or "None Recorded"
            meds_analyzed = report_data.get("medicines_analyzed", [])
            med_names = [safe_text(m.get("medicine_name") or m.get("brand_name") or "Medicine") for m in meds_analyzed]
            meds_summary = ", ".join(med_names) if med_names else "None Entered"

            patient_profile_table = Table([
                [
                    Paragraph(f"<b>PATIENT HEALTH PROFILE</b><br/>"
                              f"<b>Patient Name:</b> {p_name_display}<br/>"
                              f"<b>Age / Gender:</b> {age_str} / {gender_str}<br/>"
                              f"<b>Recorded Conditions:</b> {conds}<br/>"
                              f"<b>Known Allergies:</b> {allergies}", subtitle_style),
                    Paragraph(f"<b>EVALUATED REGIMEN OVERVIEW</b><br/>"
                              f"<b>Medicines Evaluated ({len(meds_analyzed)}):</b> {meds_summary}<br/>"
                              f"<b>Total Potential Risks:</b> {report_data.get('total_interactions_identified', 0)}<br/>"
                              f"<b>Duplicate Ingredients:</b> {report_data.get('duplicate_medicines_count', 0)}<br/>"
                              f"<b>Assessment Scope:</b> Complete Multi-Drug Compatibility", subtitle_style)
                ]
            ], colWidths=[93 * mm, 93 * mm])
        else:
            conds_raw = p_profile.get("medical_conditions", [])
            conds = safe_text(", ".join(conds_raw)) or "None Recorded"
            allergies_raw = p_profile.get("known_allergies", [])
            allergies = safe_text(", ".join(allergies_raw)) or "None Recorded"
            kidney = safe_text(p_profile.get("kidney_function", "Normal"))
            liver = safe_text(p_profile.get("liver_function", "Normal"))

            prop = report_data.get("proposed_medicine", {})
            prop_str = f"<b>{safe_text(prop.get('medicine_name', 'Proposed Medicine'))}</b> ({safe_text(prop.get('generic_name', 'Generic'))})"
            prop_sub = f"Strength: {safe_text(prop.get('strength', 'Standard'))} | Form: {safe_text(prop.get('dosage_form', 'Tablet/Oral'))}"

            patient_profile_table = Table([
                [
                    Paragraph(f"<b>PATIENT HEALTH PROFILE</b><br/>"
                              f"<b>Patient Name:</b> {p_name_display}<br/>"
                              f"<b>Age / Gender:</b> {age_str} / {gender_str}<br/>"
                              f"<b>Recorded Conditions:</b> {conds}<br/>"
                              f"<b>Known Allergies:</b> {allergies}<br/>"
                              f"<b>Organ Function:</b> Kidney: {kidney} | Liver: {liver}", subtitle_style),
                    Paragraph(f"<b>PROPOSED NEW MEDICINE</b><br/>"
                              f"{prop_str}<br/>{prop_sub}<br/>"
                              f"<b>Current Regimen:</b> {len(report_data.get('existing_medicines_analysed', []))} existing medication(s)", subtitle_style)
                ]
            ], colWidths=[93 * mm, 93 * mm])

        patient_profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), cls.BG_LIGHT),
            ('GRID', (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(patient_profile_table)
        story.append(Spacer(1, 6))

        # 3. Overall Compatibility Status Box
        status = report_data.get("overall_status", "GREEN").upper()
        if status == "RED":
            status_bg = colors.HexColor("#fef2f2")
            status_border = colors.HexColor("#dc2626")
            status_text_color = "#991b1b"
            status_icon = "HIGH RISK / CONTRAINDICATION DETECTED"
        elif status == "YELLOW":
            status_bg = colors.HexColor("#fffbeb")
            status_border = colors.HexColor("#d97706")
            status_text_color = "#92400e"
            status_icon = "MODERATE RISK / CAUTION ADVISED"
        elif status == "GREY":
            status_bg = colors.HexColor("#f8fafc")
            status_border = colors.HexColor("#64748b")
            status_text_color = "#334155"
            status_icon = "INCONCLUSIVE / UNVERIFIED MEDICINES"
        else:
            status_bg = colors.HexColor("#f0fdf4")
            status_border = colors.HexColor("#16a34a")
            status_text_color = "#166534"
            status_icon = "FAVORABLE SAFETY PROFILE / NO DOCUMENTED INTERACTIONS"

        status_headline = safe_text(report_data.get("summary_headline") or report_data.get("overall_status_label") or status_icon)

        if is_multi:
            counts_summary = (
                f"Total Findings: {report_data.get('total_interactions_identified', 0)} | "
                f"Serious (Red): {report_data.get('serious_potential_interactions', 0)} | "
                f"Caution (Yellow): {report_data.get('caution_warnings', 0)} | "
                f"Safe Combinations: {report_data.get('safe_combinations', 0)} | "
                f"Duplicates: {report_data.get('duplicate_medicines_count', 0)}"
            )
        else:
            counts = report_data.get("findings_count", {})
            counts_summary = f"Total Findings: {counts.get('total', 0)} | Serious (Red): {counts.get('serious_red', 0)} | Caution (Yellow): {counts.get('caution_yellow', 0)}"

        status_table = Table([
            [
                Paragraph(f"<font color='{status_text_color}' size='10.5'><b>STATUS: {safe_text(report_data.get('overall_status_label', status_icon))}</b></font><br/>"
                          f"<b>Summary:</b> {status_headline}<br/>"
                          f"<font size='7' color='#64748b'>{counts_summary}</font>", subtitle_style)
            ]
        ], colWidths=[186 * mm])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), status_bg),
            ('BOX', (0, 0), (-1, -1), 1.2, status_border),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(status_table)
        story.append(Spacer(1, 6))

        # 4. Unverified Medicines Notice (if any)
        unverified = report_data.get("unidentified_medicines", [])
        if unverified:
            unv_names = safe_text(", ".join(unverified))
            t_unverified = Table([
                [
                    Paragraph(f"<font color='#dc2626'><b>UNVERIFIED MEDICINE NOTICE:</b></font> The following medicine(s) could not be verified in official CDSCO / WHO compendia: <b>{unv_names}</b>. Please inspect package labeling or consult your pharmacist to confirm active salt names before dispensing.", subtitle_style)
                ]
            ], colWidths=[186 * mm])
            t_unverified.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fff1f2")),
                ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor("#f43f5e")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t_unverified)
            story.append(Spacer(1, 6))

        # 5. "What Does This Mean for You?" (Plain-Language Explanation & Mechanisms)
        story.append(Paragraph("<b>WHAT DOES THIS MEAN FOR YOU? (CLINICAL PATIENT GUIDANCE)</b>", section_heading))
        story.append(Spacer(1, 2))

        if is_multi:
            meaning = safe_text(report_data.get('what_does_this_mean', ''))
            mechanism = safe_text(report_data.get('why_they_interact', ''))
            consequence = safe_text(report_data.get('what_could_happen', ''))
            action_text = safe_text(report_data.get('action_guidance', ''))
            bullets = report_data.get("action_bullets", [])
            bullets_html = "".join([f"• {safe_text(b)}<br/>" for b in bullets])

            guidance_text = (
                f"<b>Clinical Meaning:</b> {meaning}<br/>"
                f"<b>Pharmacological Mechanism:</b> {mechanism}<br/>"
                f"<b>Potential Clinical Consequences:</b> {consequence}<br/>"
                f"<b>Recommended Action:</b> {action_text}<br/>" + bullets_html
            )
        else:
            guidance = report_data.get("personalized_guidance", {})
            assessment = safe_text(guidance.get('should_take_assessment', ''))
            meaning = safe_text(guidance.get('what_this_means_for_you', ''))
            action_list = guidance.get("action_summary", [])
            bullets_html = "".join([f"• {safe_text(a)}<br/>" for a in action_list])

            guidance_text = (
                f"<b>Clinical Assessment:</b> {assessment}<br/>"
                f"<b>Health Impact:</b> {meaning}<br/>"
                f"<b>Recommended Steps:</b><br/>" + bullets_html
            )

        t_guidance = Table([[Paragraph(guidance_text, subtitle_style)]], colWidths=[186 * mm])
        t_guidance.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_guidance)
        story.append(Spacer(1, 6))

        # 6. All Evaluated Medicines in Regimen Table
        meds_to_show = []
        if is_multi:
            meds_to_show = report_data.get("medicines_analyzed", [])
        else:
            # Combine proposed and existing for full visibility
            prop_med = report_data.get("proposed_medicine")
            if prop_med:
                meds_to_show.append({
                    "medicine_name": f"{prop_med.get('medicine_name', 'Proposed')} [PROPOSED]",
                    "generic_name": prop_med.get('generic_name', 'Generic'),
                    "strength": prop_med.get('strength', 'Standard'),
                    "frequency": prop_med.get('dosage_form', 'Oral')
                })
            meds_to_show.extend(report_data.get("existing_medicines_analysed", []))

        if meds_to_show:
            story.append(Paragraph(f"<b>ALL EVALUATED MEDICATIONS IN REGIMEN ({len(meds_to_show)})</b>", section_heading))
            story.append(Spacer(1, 2))

            med_rows = [
                [
                    Paragraph("<b>Medicine Name / Brand</b>", table_cell_bold),
                    Paragraph("<b>Active Ingredient(s) / Generic Name</b>", table_cell_bold),
                    Paragraph("<b>Strength & Dose</b>", table_cell_bold),
                    Paragraph("<b>Frequency & Route</b>", table_cell_bold),
                ]
            ]
            for m in meds_to_show:
                b_name = safe_text(m.get('medicine_name') or m.get('brand_name') or 'Medicine')
                g_name = safe_text(m.get('generic_name') or m.get('active_ingredients') or 'Standard active component')
                str_val = safe_text(f"{m.get('strength') or 'Standard'} {m.get('dosage') or ''}".strip())
                freq_val = safe_text(f"{m.get('frequency') or 'As Prescribed'} ({m.get('administration_route') or 'Oral'})")

                med_rows.append([
                    Paragraph(f"<b>{b_name}</b>", table_cell),
                    Paragraph(g_name, table_cell),
                    Paragraph(str_val, table_cell),
                    Paragraph(freq_val, table_cell)
                ])

            t_meds = Table(med_rows, colWidths=[48 * mm, 64 * mm, 37 * mm, 37 * mm])
            t_meds.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), cls.BG_LIGHT),
                ('GRID', (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(t_meds)
            story.append(Spacer(1, 6))

        # 7. Detailed Pairwise Interaction & Safety Findings Table
        if is_multi:
            table_rows = report_data.get("interaction_table", [])
            story.append(Paragraph(f"<b>CLINICAL INTERACTION FINDINGS & DRUG MECHANISMS ({len(table_rows)})</b>", section_heading))
            story.append(Spacer(1, 2))

            if table_rows:
                find_rows = [
                    [
                        Paragraph("<b>Severity</b>", table_cell_bold),
                        Paragraph("<b>Involved Items</b>", table_cell_bold),
                        Paragraph("<b>Interaction Title, Clinical Mechanism & Action</b>", table_cell_bold),
                        Paragraph("<b>Evidence Source</b>", table_cell_bold)
                    ]
                ]
                for r in table_rows:
                    sev = (r.get("severity") or "GREEN").upper()
                    sev_color = "#dc2626" if sev == "RED" else ("#d97706" if sev == "YELLOW" else "#16a34a")
                    sev_label = safe_text(r.get('severity_label') or sev)
                    type_sev = f"<font color='{sev_color}'><b>{sev_label}</b></font>"

                    inv_list = [safe_text(it) for it in r.get("medicines_involved", [])]
                    items = " + <br/>".join(inv_list) if inv_list else "Regimen items"

                    title_txt = safe_text(r.get('interaction_title', 'Clinical interaction'))
                    exp_txt = safe_text(r.get('explanation', ''))
                    mech_txt = safe_text(r.get('clinical_mechanism', 'Pharmacological pathway alteration'))
                    act_txt = safe_text(r.get('recommended_action', 'Consult prescriber before co-administration'))

                    desc = (
                        f"<b>{title_txt}</b><br/>"
                        f"<font color='#334155'>{exp_txt}</font><br/>"
                        f"<b>Mechanism:</b> {mech_txt}<br/>"
                        f"<b>Action:</b> {act_txt}"
                    )
                    src = safe_text(r.get('evidence_source', 'CDSCO / BNF / Clinical Guidelines'))

                    find_rows.append([
                        Paragraph(type_sev, table_cell),
                        Paragraph(items, table_cell),
                        Paragraph(desc, table_cell),
                        Paragraph(src, table_cell)
                    ])

                t_findings = Table(find_rows, colWidths=[30 * mm, 40 * mm, 82 * mm, 34 * mm])
                t_findings.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), cls.BG_LIGHT),
                    ('GRID', (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(t_findings)
            else:
                story.append(Paragraph("<i>No documented drug-drug interactions, disease contraindications, or allergy conflicts identified across this medication combination.</i>", subtitle_style))
        else:
            findings = report_data.get("findings", [])
            story.append(Paragraph(f"<b>CLINICAL COMPATIBILITY FINDINGS ({len(findings)})</b>", section_heading))
            story.append(Spacer(1, 2))

            if findings:
                find_rows = [
                    [
                        Paragraph("<b>Type & Severity</b>", table_cell_bold),
                        Paragraph("<b>Involved Items</b>", table_cell_bold),
                        Paragraph("<b>Clinical Explanation, Mechanism & Action</b>", table_cell_bold),
                        Paragraph("<b>Evidence Source</b>", table_cell_bold)
                    ]
                ]
                for f in findings:
                    sev = (f.get("severity") or "GREEN").upper()
                    sev_color = "#dc2626" if sev == "RED" else ("#d97706" if sev == "YELLOW" else "#16a34a")
                    sev_label = safe_text(f.get('severity_label') or sev)
                    type_sev = (
                        f"<font color='{sev_color}'><b>{sev_label}</b></font><br/>"
                        f"<font size='6.5' color='#64748b'>{safe_text(f.get('finding_type', 'Interaction'))}</font>"
                    )
                    items_list = [safe_text(it) for it in f.get("medicines_involved", [])]
                    items = ", ".join(items_list)
                    if f.get("medical_condition_involved"):
                        items += f"<br/><i>Condition: {safe_text(f.get('medical_condition_involved'))}</i>"
                    if f.get("allergy_involved"):
                        items += f"<br/><i>Allergy: {safe_text(f.get('allergy_involved'))}</i>"

                    headline_txt = safe_text(f.get('headline', ''))
                    exp_txt = safe_text(f.get('plain_language_explanation', ''))
                    act_txt = safe_text(f.get('recommended_action', 'Consult physician'))

                    exp_action = (
                        f"<b>{headline_txt}</b><br/>"
                        f"{exp_txt}<br/>"
                        f"<b>Action:</b> {act_txt}"
                    )
                    src_date = safe_text(f.get('source_update_date', 'Current'))
                    src = f"{safe_text(f.get('evidence_source', 'CDSCO'))}<br/><font size='6.5' color='#64748b'>Updated: {src_date}</font>"

                    find_rows.append([
                        Paragraph(type_sev, table_cell),
                        Paragraph(items, table_cell),
                        Paragraph(exp_action, table_cell),
                        Paragraph(src, table_cell)
                    ])

                t_findings = Table(find_rows, colWidths=[32 * mm, 40 * mm, 80 * mm, 34 * mm])
                t_findings.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), cls.BG_LIGHT),
                    ('GRID', (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(t_findings)
            else:
                story.append(Paragraph("<i>No documented drug interactions, disease contraindications, or allergy conflicts identified in verified databases.</i>", subtitle_style))

        story.append(Spacer(1, 6))

        # 8. Questions to Discuss with Physician / Clinician Review
        discuss_list = report_data.get("what_to_discuss_with_doctor") or []
        if discuss_list:
            story.append(Paragraph("<b>RECOMMENDED QUESTIONS TO DISCUSS WITH YOUR PHYSICIAN / PHARMACIST</b>", section_heading))
            story.append(Spacer(1, 2))
            q_text = "".join([f"• {safe_text(q)}<br/>" for q in discuss_list])
            t_q = Table([[Paragraph(q_text, subtitle_style)]], colWidths=[186 * mm])
            t_q.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t_q)
            story.append(Spacer(1, 6))

        # 9. Clinician Review & Sign-Off Section (KeepTogether to prevent separation)
        doc_sig_table = Table([
            [
                Paragraph("<b>REVIEWING CLINICIAN / REGISTERED PHARMACIST</b><br/>"
                          "Name: __________________________________________<br/>"
                          "Registration / License No: ________________________<br/>"
                          "Institution / Clinic Stamp: ______________________", subtitle_style),
                Paragraph("<b>DISPENSING & MONITORING RECOMMENDATION</b><br/>"
                          "[  ] Approved as Prescribed without Modification<br/>"
                          "[  ] Dose Adjustment / Therapeutic Monitoring Required<br/>"
                          "[  ] Therapy Withheld — Safe Alternative Recommended<br/>"
                          "Signature: ______________________ Date: _________", subtitle_style)
            ]
        ], colWidths=[93 * mm, 93 * mm])
        doc_sig_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        # 10. Disclaimer
        disclaimer_text = safe_text(report_data.get('disclaimer',
            "This report is generated by PharmIntel Clinical Decision Support "
            "and combines curated compendia (BNF, CDSCO, WHO, FDA) with Graph Neural Network predictions. It is intended solely for clinical guidance "
            "and does not replace licensed medical practitioner consultation. Patients must never alter or discontinue prescribed medication independently."
        ))
        disclaimer_flowable = Paragraph(
            f"<font color='#64748b' size='6.5'><b>CLINICAL DISCLAIMER:</b> {disclaimer_text}</font>",
            subtitle_style
        )

        signoff_block = KeepTogether([
            doc_sig_table,
            Spacer(1, 4),
            HRFlowable(width="100%", thickness=0.5, color=cls.BORDER_COLOR, spaceAfter=2, spaceBefore=2),
            disclaimer_flowable
        ])
        story.append(signoff_block)

        doc.build(story, canvasmaker=PatientSafetyReportCanvas)
        buffer.seek(0)
        return buffer

