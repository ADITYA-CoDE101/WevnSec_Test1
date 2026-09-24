"""In-memory, paginated scan reports; no uploaded files or external asset fetches."""
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether


def build_pdf(scan):
    output = BytesIO()
    brand = colors.HexColor('#0284c7')
    ink = colors.HexColor('#16202a')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('ReportTitle', fontName='Helvetica-Bold', fontSize=26, leading=32, textColor=ink, spaceAfter=12, splitLongWords=True))
    styles.add(ParagraphStyle('ReportBody', fontSize=10, leading=15, textColor=ink, spaceAfter=9))
    styles.add(ParagraphStyle('ReportCode', fontName='Courier', fontSize=8, leading=12, textColor=ink, backColor=colors.HexColor('#f3f6f8'), borderPadding=8, spaceAfter=12, splitLongWords=True))
    styles.add(ParagraphStyle('ReportLabel', fontSize=9, leading=13, textColor=brand, spaceAfter=8))
    styles.add(ParagraphStyle('ReportHeading', fontName='Helvetica-Bold', fontSize=12, leading=17, spaceBefore=14, spaceAfter=8, textColor=ink, keepWithNext=True))

    def p(value, style='ReportBody'):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), styles[style])

    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=28*mm, bottomMargin=24*mm, title=f'WevnSec Security Report - {scan.target}', author='WevnSec')
    counts = scan.counts
    failed = sum(counts.get(s, 0) for s in ('critical','high','medium','low'))
    story = [p('WEBSITE SECURITY ASSESSMENT', 'ReportLabel'), p(scan.target, 'ReportTitle'),
             p(f"Scanned {scan.created_at.strftime('%d %B %Y, %H:%M UTC')}  |  Report {scan.share_id}"), Spacer(1, 6*mm)]
    metrics = Table([[p(f'GRADE {scan.grade}', 'ReportHeading'), p(f'{scan.score}/100', 'ReportHeading'), p(f'{failed} findings', 'ReportHeading'), p(f"{counts.get('passed',0)} passed", 'ReportHeading')]], colWidths=[doc.width/4]*4)
    metrics.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#eef6fa')), ('BOX',(0,0),(-1,-1),0.5,brand), ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),12)]))
    story += [metrics, Spacer(1,7*mm), p('Executive summary', 'ReportHeading'),
              p(f"This point-in-time assessment performed {len(scan.checks)} automated checks. It identified {counts.get('critical',0)} critical, {counts.get('high',0)} high, {counts.get('medium',0)} medium and {counts.get('low',0)} low-severity findings, plus {counts.get('warning',0)} warnings."),
              p('Scope & limitations', 'ReportHeading'), p('External checks cover TLS, transport, response security headers, cookie flags, CORS, and exposed configuration paths. This is not an exhaustive penetration test, compliance certification, or guarantee that the site is secure. Warnings indicate observations or checks requiring manual verification. Findings should be validated before remediation.'),
              p('Scoring', 'ReportHeading'), p('Starting at 100: critical -25, high -15, medium -8, low -3, warning -3; minimum score 5. Grades: A+ 95-100, A 85-94, B 70-84, C 55-69, D 40-54, F below 40.'),
              p('Findings & remediation', 'ReportHeading')]
    rank = {'fail':0,'warn':1,'pass':2}
    severity_rank = {'critical':0,'high':1,'medium':2,'low':3,'none':4}
    checks = sorted(scan.checks, key=lambda c:(rank.get(c['status'],3),severity_rank.get(c['severity'],4)))
    for i, check in enumerate(checks, 1):
        story.append(p(f"{i:02d}  {check['name']}", 'ReportHeading'))
        story.append(p(f"{check['status'].upper()}  /  {check['severity'].upper()}  /  {check['category']}  /  {check['id']}", 'ReportLabel'))
        story.append(p(check['detail']))
        if check.get('fix'):
            story += [p('Recommended remediation', 'ReportLabel'), p(check['fix'], 'ReportCode')]

    def page_frame(canvas, document):
        width, height = A4
        canvas.saveState()
        canvas.setFillColor(ink)
        canvas.setFont('Helvetica-Bold', 15)
        canvas.drawString(20*mm, height-17*mm, 'WevnSec')
        canvas.setStrokeColor(brand)
        canvas.setLineWidth(1)
        canvas.line(20*mm,height-21*mm,width-20*mm,height-21*mm)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(20*mm,15*mm,f'WevnSec | {scan.share_id} | Automated assessment')
        canvas.drawRightString(width-20*mm,15*mm,f'Page {document.page}')
        canvas.restoreState()

    doc.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    return output.getvalue()