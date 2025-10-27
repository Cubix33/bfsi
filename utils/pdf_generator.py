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
    
    # Create PDF
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for PDF elements
    elements = []
    
    # Styles
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
    
    # Add Logo/Header
    header_text = "🏦 TATA CAPITAL"
    header = Paragraph(header_text, title_style)
    elements.append(header)
    
    # Add subtitle
    subtitle = Paragraph("<b>LOAN SANCTION LETTER</b>", ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#5c6bc0'),
        alignment=TA_CENTER,
        spaceAfter=20
    ))
    elements.append(subtitle)
    
    # Add date and reference
    date_ref = Paragraph(
        f"<b>Date:</b> {datetime.now().strftime('%d %B %Y')}<br/>"
        f"<b>Reference No:</b> TC/PL/{datetime.now().strftime('%Y%m%d')}/{customer_data['id']}",
        normal_style
    )
    elements.append(date_ref)
    elements.append(Spacer(1, 20))
    
    # Customer Details Section
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
    
    # Loan Details Section
    elements.append(Paragraph("💰 Loan Details", heading_style))
    
    # Calculate total payable
    total_payable = loan_details['emi'] * loan_details['tenure']
    total_interest = total_payable - loan_details['amount']
    
    loan_table_data = [
        ['Loan Amount:', f"₹{loan_details['amount']:,}"],
        ['Interest Rate:', f"{loan_details['interest_rate']}% per annum"],
        ['Loan Tenure:', f"{loan_details['tenure']} months ({loan_details['tenure']//12} years)"],
        ['Monthly EMI:', f"₹{loan_details['emi']:,}"],
        ['Total Interest:', f"₹{total_interest:,}"],
        ['Total Payable:', f"₹{total_payable:,}"],
        ['Loan Purpose:', loan_details['purpose'].replace('_', ' ').title()],
        ['Processing Fee:', '₹0 (Waived)'],
        ['Disbursement Mode:', 'Direct Bank Transfer']
    ]
    
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
        ('BACKGROUND', (-1, 3), (-1, 3), colors.HexColor('#c5e1a5')),  # Highlight EMI
        ('FONTNAME', (-1, 3), (-1, 3), 'Helvetica-Bold')
    ]))
    
    elements.append(loan_table)
    elements.append(Spacer(1, 20))
    
    # Terms & Conditions
    elements.append(Paragraph("📜 Terms & Conditions", heading_style))
    
    terms = [
        "1. The loan is subject to the terms and conditions mentioned in the loan agreement.",
        "2. EMI payments must be made on or before the 5th of every month.",
        "3. Prepayment is allowed after 6 months with no additional charges.",
        "4. Late payment will attract a penalty of 2% per month on the overdue amount.",
        "5. The loan is subject to final documentation and verification.",
        "6. Disbursement will be done within 2-3 business days post-documentation.",
        "7. This sanction is valid for 30 days from the date of issue."
    ]
    
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
    
    # Signature Section
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
    
    # Footer
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
    
    # Build PDF
    doc.build(elements)
    
    print(f"\n✅ Sanction letter generated: {filename}\n")
    
    return filename


# Test
if __name__ == "__main__":
    test_customer = {
        "id": "C01",
        "name": "Riya Sharma",
        "phone": "7303201137",
        "email": "riya.sharma@email.com",
        "address": "Block A, Sector 15, Rohini",
        "city": "Delhi"
    }
    
    test_loan = {
        "amount": 500000,
        "tenure": 24,
        "purpose": "wedding",
        "interest_rate": 11.0,
        "emi": 23303
    }
    
    generate_sanction_letter(test_customer, test_loan)
    print("Open the PDF with a PDF reader (not text editor)!")
