from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os


def generate_sanction_letter(customer_data, loan_details):
    """
    Generate professional PDF sanction letter
    """
    
    # Create sanction_letters folder if it doesn't exist
    if not os.path.exists('sanction_letters'):
        os.makedirs('sanction_letters')
    
    # Generate filename
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"sanction_letters/SanctionLetter_{customer_data['name'].replace(' ', '_')}_{date_str}.pdf"
    
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#283593'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        leading=14
    )
    
    header_text = "🏦 TATA CAPITAL"
    header = Paragraph(header_text, title_style)
    elements.append(header)
    
    # --- UPDATED: Check for loan type for title ---
    loan_type = loan_details.get("loan_type", "personal").upper()
    if "SECURED" in loan_type:
        subtitle_text = "<b>SECURED LOAN SANCTION LETTER</b>"
    else:
        subtitle_text = "<b>PERSONAL LOAN SANCTION LETTER</b>"
        
    subtitle = Paragraph(subtitle_text, ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#5c6bc0'),
        alignment=TA_CENTER,
        spaceAfter=20
    ))
    elements.append(subtitle)
    
    date_ref = Paragraph(
        f"<b>Date:</b> {datetime.now().strftime('%d %B %Y')}<br/>"
        f"<b>Reference No:</b> TC/PL/{datetime.now().strftime('%Y%m%d')}/{customer_data['id']}",
        normal_style
    )
    elements.append(date_ref)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("📋 Customer Details", heading_style))
    
    customer_table_data = [
        ['Customer Name:', customer_data['name']],
        ['Customer ID:', customer_data['id']],
        ['Phone Number:', customer_data['phone']],
        ['Email:', customer_data.get('email', 'N/A')],
        ['Address:', customer_data['address']],
        ['City:', customer_data['city']]
    ]
    
    customer_table = Table(customer_table_data, colWidths=[2*inch, 4*inch])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
    ]))
    
    elements.append(customer_table)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("💰 Loan Details", heading_style))
    
    total_payable = loan_details['emi'] * loan_details['tenure']
    total_interest = total_payable - loan_details['amount']
    
    # --- UPDATED: Add Secured Loan fields ---
    loan_table_data = [
        ['Loan Amount:', f"₹{loan_details['amount']:,}"],
        ['Interest Rate:', f"{loan_details['interest_rate']}% per annum"],
        ['Loan Tenure:', f"{loan_details['tenure']} months ({loan_details['tenure']//12} years)"],
        ['Monthly EMI:', f"₹{loan_details['emi']:,}"],
        ['Total Interest:', f"₹{total_interest:,.0f}"], # Use .0f for cleaner formatting
        ['Total Payable:', f"₹{total_payable:,.0f}"], # Use .0f
        ['Loan Purpose:', loan_details['purpose'].replace('_', ' ').title()]
    ]
    
    # Dynamically add secured loan info if it exists
    if "secured" in loan_type.lower():
        loan_table_data.append(['Loan Type:', 'Secured Loan'])
        loan_table_data.append(['Collateral Pledged:', loan_details.get('collateral', 'N/A')])
    else:
        loan_table_data.append(['Loan Type:', 'Unsecured Personal Loan'])
        
    loan_table_data.append(['Processing Fee:', '₹0 (Waived)'])
    loan_table_data.append(['Disbursement Mode:', 'Direct Bank Transfer'])
    # --- END OF UPDATE ---
    
    loan_table = Table(loan_table_data, colWidths=[2*inch, 4*inch])
    loan_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('BACKGROUND', (0, 3), (1, 3), colors.HexColor('#c5e1a5')),  # Highlight EMI
        ('FONTNAME', (0, 3), (1, 3), 'Helvetica-Bold')
    ]))
    
    elements.append(loan_table)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("📜 Terms & Conditions", heading_style))
    
    terms = [
        "1. The loan is subject to the terms and conditions mentioned in the loan agreement.",
        "2. EMI payments must be made on or before the 5th of every month.",
        "3. Prepayment is allowed after 6 months with no additional charges.",
        "4. Late payment will attract a penalty of 2% per month on the overdue amount.",
        "5. The loan is subject to final documentation and verification.",
        "6. Disbursement will be done within 2-3 business days post-documentation."
    ]
    
    if "secured" in loan_type.lower():
        terms.append("7. The approved loan amount is secured against the collateral provided: " + loan_details.get('collateral', 'N/A') + ".")
        terms.append("8. This sanction is valid for 30 days from the date of issue.")
    else:
        terms.append("7. This sanction is valid for 30 days from the date of issue.")
        
    for term in terms:
        elements.append(Paragraph(term, ParagraphStyle(
            'Terms',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            leftIndent=0,
            spaceAfter=4
        )))
    
    elements.append(Spacer(1, 30))
    
    elements.append(Paragraph("✍️ Authorized Signatory", heading_style))
    elements.append(Spacer(1, 40))
    
    signature_data = [
        ['_____________________', '_____________________'],
        ['Authorized Signature', 'Customer Signature'],
        ['Tata Capital', customer_data['name']]
    ]
    
    signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(signature_table)
    elements.append(Spacer(1, 20))
    
    footer = Paragraph(
        "<i>This is a system-generated document and does not require a physical signature for validation.</i><br/>"
        "<b>Tata Capital Limited</b> | Customer Care: 1800-123-4567 | www.tatacapital.com",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
    )
    elements.append(footer)
    
    doc.build(elements)
    
    print(f"\n✅ Sanction letter generated: {filename}\n")
    
    return filename