"""
Research Report PDF Generator
Generates professional PDF reports similar to research firm reports
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from io import BytesIO
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logging.warning("reportlab not installed. PDF generation will not work.")

logger = logging.getLogger(__name__)

class ResearchReportPDFGenerator:
    """Generate PDF reports from research report data"""
    
    def __init__(self):
        if not HAS_REPORTLAB:
            logger.warning("reportlab not available. Install with: pip install reportlab")
    
    def generate_pdf(
        self,
        report_data: Dict,
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Generate PDF from research report data
        
        Args:
            report_data: Complete research report dictionary
            output_path: Optional file path to save PDF
        
        Returns:
            BytesIO buffer with PDF content
        """
        if not HAS_REPORTLAB:
            raise ImportError("reportlab library not installed. Install with: pip install reportlab")
        
        try:
            buffer = BytesIO()
            
            # Create PDF document
            if output_path:
                doc = SimpleDocTemplate(output_path, pagesize=A4)
            else:
                doc = SimpleDocTemplate(buffer, pagesize=A4)
            
            # Container for PDF elements
            story = []
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Title style
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1E40AF'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            # Heading style
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#1E40AF'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # Subheading style
            subheading_style = ParagraphStyle(
                'CustomSubHeading',
                parent=styles['Heading3'],
                fontSize=14,
                textColor=colors.HexColor('#374151'),
                spaceAfter=8
            )
            
            # Normal text style
            normal_style = styles['Normal']
            
            # Add title
            title = f"Research Report: {report_data.get('company_name', report_data.get('symbol', 'Stock'))}"
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Add report metadata
            report_date = report_data.get('report_date', datetime.now().isoformat())
            try:
                date_obj = datetime.fromisoformat(report_date.replace('Z', '+00:00'))
                date_str = date_obj.strftime("%B %d, %Y")
            except:
                date_str = report_date
            
            metadata = f"<b>Symbol:</b> {report_data.get('symbol', 'N/A')} | "
            metadata += f"<b>Current Price:</b> ₹{report_data.get('current_price', 0):.2f} | "
            metadata += f"<b>Date:</b> {date_str}"
            story.append(Paragraph(metadata, normal_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Recommendation Banner
            recommendation = report_data.get('sections', {}).get('recommendation', {})
            if recommendation:
                rec_type = recommendation.get('recommendation', 'HOLD')
                confidence = recommendation.get('confidence', 0)
                target_price = recommendation.get('target_price')
                upside = recommendation.get('potential_upside')
                
                rec_color = colors.HexColor('#10B981') if rec_type == 'BUY' else colors.HexColor('#EF4444') if rec_type == 'SELL' else colors.HexColor('#F59E0B')
                
                rec_text = f"<b>Recommendation: {rec_type}</b> (Confidence: {confidence}%)"
                if target_price:
                    rec_text += f"<br/>Target Price: ₹{target_price:.2f}"
                if upside:
                    rec_text += f" | Potential Upside: {upside:.2f}%"
                
                rec_para = Paragraph(rec_text, ParagraphStyle(
                    'Recommendation',
                    parent=normal_style,
                    fontSize=14,
                    textColor=rec_color,
                    backColor=colors.HexColor('#F3F4F6'),
                    borderPadding=10,
                    spaceAfter=20
                ))
                story.append(rec_para)
                story.append(Spacer(1, 0.2*inch))
            
            # Financial Ratios Section
            financial_ratios = report_data.get('sections', {}).get('financial_ratios', {})
            if financial_ratios and financial_ratios.get('has_data'):
                story.append(Paragraph("Financial Ratios", heading_style))
                story.append(Spacer(1, 0.1*inch))
                
                ratios = financial_ratios.get('ratios', {})
                if ratios:
                    ratio_data = [['Metric', 'Value']]
                    for key, value in ratios.items():
                        if isinstance(value, (int, float)):
                            if 'cap' in key.lower() or 'price' in key.lower():
                                display_value = f"₹{(value / 10000):.2f} Cr"
                            else:
                                display_value = f"{value:.2f}"
                        else:
                            display_value = str(value)
                        ratio_data.append([key.replace('_', ' ').title(), display_value])
                    
                    ratio_table = Table(ratio_data, colWidths=[3*inch, 2*inch])
                    ratio_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                    ]))
                    story.append(ratio_table)
                    story.append(Spacer(1, 0.3*inch))
            
            # Executive Summary
            executive_summary = report_data.get('sections', {}).get('executive_summary', {})
            if executive_summary and executive_summary.get('has_data'):
                story.append(PageBreak())
                story.append(Paragraph("Executive Summary", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(executive_summary.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.3*inch))
            
            # Key Metrics Dashboard
            key_metrics = report_data.get('sections', {}).get('key_metrics_dashboard', {})
            if key_metrics and key_metrics.get('has_data'):
                story.append(Paragraph("Key Metrics Dashboard", heading_style))
                story.append(Spacer(1, 0.1*inch))
                
                metrics = key_metrics.get('metrics', {})
                if metrics:
                    metrics_data = [['Metric', 'Value']]
                    for key, value in metrics.items():
                        if value is not None:
                            if isinstance(value, (int, float)):
                                if 'cap' in key.lower() or 'price' in key.lower():
                                    display_value = f"₹{(value / 10000):.2f} Cr"
                                else:
                                    display_value = f"{value:.2f}"
                            else:
                                display_value = str(value)
                            metrics_data.append([key.replace('_', ' ').title(), display_value])
                    
                    if len(metrics_data) > 1:
                        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
                        metrics_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 11),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                        ]))
                        story.append(metrics_table)
                        story.append(Spacer(1, 0.3*inch))
            
            # Financial Trends
            financial_trends = report_data.get('sections', {}).get('financial_trends', {})
            if financial_trends and financial_trends.get('has_data'):
                story.append(Paragraph("Financial Trends", heading_style))
                story.append(Spacer(1, 0.1*inch))
                
                quarterly_trends = financial_trends.get('trends', {}).get('quarterly', [])
                if quarterly_trends:
                    trends_data = [['Period', 'Revenue (₹ Cr)', 'Net Profit (₹ Cr)', 'Net Margin (%)', 'Op Margin (%)']]
                    for trend in quarterly_trends[:8]:
                        period = trend.get('period', 'N/A')
                        # Format period for display
                        if isinstance(period, str) and '-' in period:
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(period.replace('Z', '+00:00'))
                                period = dt.strftime('%b %Y')
                            except:
                                pass
                        
                        revenue = f"{trend.get('revenue', 0):.2f}" if trend.get('revenue') else 'N/A'
                        profit = f"{trend.get('net_profit', 0):.2f}" if trend.get('net_profit') else 'N/A'
                        net_margin = f"{trend.get('net_margin', 0):.2f}%" if trend.get('net_margin') is not None else 'N/A'
                        op_margin = f"{trend.get('operating_margin', 0):.2f}%" if trend.get('operating_margin') is not None else 'N/A'
                        trends_data.append([period, revenue, profit, net_margin, op_margin])
                    
                    if len(trends_data) > 1:
                        trends_table = Table(trends_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1*inch, 1*inch])
                        trends_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                        ]))
                        story.append(trends_table)
                        story.append(Spacer(1, 0.3*inch))
            
            # Comparison Table
            comparison_table = report_data.get('sections', {}).get('comparison_table', {})
            if comparison_table and comparison_table.get('has_data'):
                story.append(Paragraph("Quarterly Comparison", heading_style))
                story.append(Spacer(1, 0.1*inch))
                
                comparison = comparison_table.get('comparison', {})
                quarterly = comparison.get('quarterly', {})
                if quarterly:
                    comp_data = [['Metric', 'Current', 'Previous', 'Change']]
                    
                    if quarterly.get('current', {}).get('revenue'):
                        current_rev = quarterly.get('current', {}).get('revenue', 0)
                        prev_rev = quarterly.get('previous', {}).get('revenue', 0)
                        change_pct = quarterly.get('revenue_change_pct', 0)
                        comp_data.append([
                            'Revenue (₹ Cr)',
                            f"₹{(current_rev / 10000):.2f}",
                            f"₹{(prev_rev / 10000):.2f}" if prev_rev else 'N/A',
                            f"{change_pct:+.2f}%" if change_pct else 'N/A'
                        ])
                    
                    if quarterly.get('current', {}).get('net_profit'):
                        current_prof = quarterly.get('current', {}).get('net_profit', 0)
                        prev_prof = quarterly.get('previous', {}).get('net_profit', 0)
                        change_pct = quarterly.get('profit_change_pct', 0)
                        comp_data.append([
                            'Net Profit (₹ Cr)',
                            f"₹{(current_prof / 10000):.2f}",
                            f"₹{(prev_prof / 10000):.2f}" if prev_prof else 'N/A',
                            f"{change_pct:+.2f}%" if change_pct else 'N/A'
                        ])
                    
                    if len(comp_data) > 1:
                        comp_table = Table(comp_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
                        comp_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                        ]))
                        story.append(comp_table)
                        story.append(Spacer(1, 0.3*inch))
            
            # Screener Data Sections (Growth Metrics, Balance Sheet, Cash Flows, Shareholding)
            detailed_research = report_data.get('sections', {}).get('detailed_company_research', {})
            screener_data = None
            if detailed_research and detailed_research.get('full_research'):
                screener_data = detailed_research.get('full_research', {}).get('screener_data', {})
            
            # Growth Metrics
            if screener_data and screener_data.get('growth_metrics'):
                story.append(Paragraph("Growth Metrics (Screener.in)", heading_style))
                story.append(Spacer(1, 0.1*inch))
                
                growth_metrics = screener_data['growth_metrics']
                growth_data = [['Metric', '10 Years', '5 Years', '3 Years', 'TTM/1Y']]
                
                # Sales Growth
                if any([growth_metrics.get('sales_growth_10y'), growth_metrics.get('sales_growth_5y'), 
                       growth_metrics.get('sales_growth_3y'), growth_metrics.get('sales_growth_ttm')]):
                    growth_data.append([
                        'Compounded Sales Growth',
                        f"{growth_metrics.get('sales_growth_10y', 0):.1f}%" if growth_metrics.get('sales_growth_10y') else 'N/A',
                        f"{growth_metrics.get('sales_growth_5y', 0):.1f}%" if growth_metrics.get('sales_growth_5y') else 'N/A',
                        f"{growth_metrics.get('sales_growth_3y', 0):.1f}%" if growth_metrics.get('sales_growth_3y') else 'N/A',
                        f"{growth_metrics.get('sales_growth_ttm', 0):.1f}%" if growth_metrics.get('sales_growth_ttm') else 'N/A'
                    ])
                
                # Profit Growth
                if any([growth_metrics.get('profit_growth_10y'), growth_metrics.get('profit_growth_5y'),
                       growth_metrics.get('profit_growth_3y'), growth_metrics.get('profit_growth_ttm')]):
                    growth_data.append([
                        'Compounded Profit Growth',
                        f"{growth_metrics.get('profit_growth_10y', 0):.1f}%" if growth_metrics.get('profit_growth_10y') else 'N/A',
                        f"{growth_metrics.get('profit_growth_5y', 0):.1f}%" if growth_metrics.get('profit_growth_5y') else 'N/A',
                        f"{growth_metrics.get('profit_growth_3y', 0):.1f}%" if growth_metrics.get('profit_growth_3y') else 'N/A',
                        f"{growth_metrics.get('profit_growth_ttm', 0):.1f}%" if growth_metrics.get('profit_growth_ttm') else 'N/A'
                    ])
                
                # Stock Price CAGR
                if any([growth_metrics.get('price_cagr_10y'), growth_metrics.get('price_cagr_5y'),
                       growth_metrics.get('price_cagr_3y'), growth_metrics.get('price_cagr_1y')]):
                    growth_data.append([
                        'Stock Price CAGR',
                        f"{growth_metrics.get('price_cagr_10y', 0):.1f}%" if growth_metrics.get('price_cagr_10y') else 'N/A',
                        f"{growth_metrics.get('price_cagr_5y', 0):.1f}%" if growth_metrics.get('price_cagr_5y') else 'N/A',
                        f"{growth_metrics.get('price_cagr_3y', 0):.1f}%" if growth_metrics.get('price_cagr_3y') else 'N/A',
                        f"{growth_metrics.get('price_cagr_1y', 0):.1f}%" if growth_metrics.get('price_cagr_1y') else 'N/A'
                    ])
                
                # ROE
                if any([growth_metrics.get('roe_10y'), growth_metrics.get('roe_5y'),
                       growth_metrics.get('roe_3y'), growth_metrics.get('roe_last_year')]):
                    growth_data.append([
                        'Return on Equity (ROE)',
                        f"{growth_metrics.get('roe_10y', 0):.1f}%" if growth_metrics.get('roe_10y') else 'N/A',
                        f"{growth_metrics.get('roe_5y', 0):.1f}%" if growth_metrics.get('roe_5y') else 'N/A',
                        f"{growth_metrics.get('roe_3y', 0):.1f}%" if growth_metrics.get('roe_3y') else 'N/A',
                        f"{growth_metrics.get('roe_last_year', 0):.1f}%" if growth_metrics.get('roe_last_year') else 'N/A'
                    ])
                
                if len(growth_data) > 1:
                    growth_table = Table(growth_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
                    growth_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                    ]))
                    story.append(growth_table)
                    story.append(Spacer(1, 0.3*inch))
            
            # Balance Sheet
            if screener_data and screener_data.get('balance_sheet'):
                balance_sheet = screener_data['balance_sheet']
                if balance_sheet and len(balance_sheet) > 0:
                    story.append(Paragraph("Balance Sheet (Screener.in)", heading_style))
                    story.append(Spacer(1, 0.1*inch))
                    
                    bs_data = [['Period', 'Equity Capital (₹ Cr)', 'Reserves (₹ Cr)', 'Borrowings (₹ Cr)']]
                    for bs in balance_sheet[:10]:  # Last 10 periods
                        equity = f"₹{(bs.get('equity_capital', 0) / 10000):.2f}" if bs.get('equity_capital') else 'N/A'
                        reserves = f"₹{(bs.get('reserves', 0) / 10000):.2f}" if bs.get('reserves') else 'N/A'
                        borrowings = f"₹{(bs.get('borrowings', 0) / 10000):.2f}" if bs.get('borrowings') else 'N/A'
                        bs_data.append([bs.get('period', 'N/A'), equity, reserves, borrowings])
                    
                    bs_table = Table(bs_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                    bs_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                    ]))
                    story.append(bs_table)
                    story.append(Spacer(1, 0.3*inch))
            
            # Cash Flows
            if screener_data and screener_data.get('cash_flows'):
                cash_flows = screener_data['cash_flows']
                if cash_flows and len(cash_flows) > 0:
                    story.append(Paragraph("Cash Flows (Screener.in)", heading_style))
                    story.append(Spacer(1, 0.1*inch))
                    
                    cf_data = [['Period', 'Operating CF (₹ Cr)', 'Investing CF (₹ Cr)', 'Financing CF (₹ Cr)']]
                    for cf in cash_flows[:10]:  # Last 10 periods
                        operating = f"₹{(cf.get('operating_cash_flow', 0) / 10000):.2f}" if cf.get('operating_cash_flow') else 'N/A'
                        investing = f"₹{(cf.get('investing_cash_flow', 0) / 10000):.2f}" if cf.get('investing_cash_flow') else 'N/A'
                        financing = f"₹{(cf.get('financing_cash_flow', 0) / 10000):.2f}" if cf.get('financing_cash_flow') else 'N/A'
                        cf_data.append([cf.get('period', 'N/A'), operating, investing, financing])
                    
                    cf_table = Table(cf_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                    cf_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                    ]))
                    story.append(cf_table)
                    story.append(Spacer(1, 0.3*inch))
            
            # Shareholding Pattern
            if screener_data and screener_data.get('detailed_shareholding'):
                shareholding = screener_data['detailed_shareholding']
                if shareholding and len(shareholding) > 0:
                    story.append(Paragraph("Shareholding Pattern (Screener.in)", heading_style))
                    story.append(Spacer(1, 0.1*inch))
                    
                    sh_data = [['Period', 'Promoters', 'FIIs', 'DIIs', 'Government', 'Public', 'Shareholders']]
                    for sh in shareholding[:12]:  # Last 12 periods
                        promoters = f"{sh.get('promoters', 0):.2f}%" if sh.get('promoters') else 'N/A'
                        fiis = f"{sh.get('fiis', 0):.2f}%" if sh.get('fiis') else 'N/A'
                        diis = f"{sh.get('diis', 0):.2f}%" if sh.get('diis') else 'N/A'
                        government = f"{sh.get('government', 0):.2f}%" if sh.get('government') else 'N/A'
                        public = f"{sh.get('public', 0):.2f}%" if sh.get('public') else 'N/A'
                        shareholders = f"{sh.get('no_of_shareholders', 0):,}" if sh.get('no_of_shareholders') else 'N/A'
                        sh_data.append([sh.get('period', 'N/A'), promoters, fiis, diis, government, public, shareholders])
                    
                    sh_table = Table(sh_data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
                    sh_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9333EA')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                    ]))
                    story.append(sh_table)
                    story.append(Spacer(1, 0.3*inch))
            
            # Quarterly P&L Section
            quarterly_pl = report_data.get('sections', {}).get('quarterly_pl', {})
            if quarterly_pl and quarterly_pl.get('has_data'):
                story.append(Paragraph("Quarterly P&L Analysis", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(quarterly_pl.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                quarters = quarterly_pl.get('quarters', [])[:8]  # Last 8 quarters
                if quarters:
                    q_data = [['Period', 'Revenue', 'Net Profit', 'EPS']]
                    for q in quarters:
                        revenue = f"₹{(q.get('revenue', 0) / 10000):.2f} Cr" if q.get('revenue') else 'N/A'
                        profit = f"₹{(q.get('net_profit', 0) / 10000):.2f} Cr" if q.get('net_profit') else 'N/A'
                        eps = f"₹{q.get('eps', 0):.2f}" if q.get('eps') else 'N/A'
                        q_data.append([q.get('period', 'N/A'), revenue, profit, eps])
                    
                    q_table = Table(q_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
                    q_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                    ]))
                    story.append(q_table)
                    story.append(Spacer(1, 0.3*inch))
            
            # Yearly P&L Section
            yearly_pl = report_data.get('sections', {}).get('yearly_pl', {})
            if yearly_pl and yearly_pl.get('has_data'):
                story.append(Paragraph("Yearly P&L Analysis", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(yearly_pl.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                years = yearly_pl.get('years', [])[:5]  # Last 5 years
                if years:
                    y_data = [['Period', 'Revenue', 'Net Profit', 'EPS']]
                    for y in years:
                        revenue = f"₹{(y.get('revenue', 0) / 10000):.2f} Cr" if y.get('revenue') else 'N/A'
                        profit = f"₹{(y.get('net_profit', 0) / 10000):.2f} Cr" if y.get('net_profit') else 'N/A'
                        eps = f"₹{y.get('eps', 0):.2f}" if y.get('eps') else 'N/A'
                        y_data.append([y.get('period', 'N/A'), revenue, profit, eps])
                    
                    y_table = Table(y_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
                    y_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                    ]))
                    story.append(y_table)
                    story.append(Spacer(1, 0.3*inch))
            
            # Detailed Company Research
            detailed_research = report_data.get('sections', {}).get('detailed_company_research', {})
            if detailed_research and detailed_research.get('has_data'):
                story.append(PageBreak())
                story.append(Paragraph("Detailed Company Research", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(detailed_research.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.2*inch))
                
                research_sections = detailed_research.get('sections', [])
                for section in research_sections:
                    story.append(Paragraph(section.get('title', ''), subheading_style))
                    
                    # Company Overview
                    if section.get('type') == 'company_overview':
                        if section.get('content'):
                            story.append(Paragraph(section.get('content', ''), normal_style))
                        if section.get('achievements'):
                            story.append(Paragraph("<b>Key Achievements:</b>", subheading_style))
                            for achievement in section.get('achievements', []):
                                story.append(Paragraph(f"• {achievement}", normal_style))
                    
                    # Business Segments
                    elif section.get('type') == 'business_segments':
                        segments = section.get('segments', [])
                        for segment in segments:
                            seg_text = f"<b>{segment.get('title', '')}</b><br/>"
                            if segment.get('revenue'):
                                seg_text += f"Revenue: {segment.get('revenue', '')}<br/>"
                            if segment.get('ebitda'):
                                seg_text += f"EBITDA: {segment.get('ebitda', '')}<br/>"
                            if segment.get('contribution'):
                                seg_text += f"Contribution: {segment.get('contribution', '')}<br/>"
                            story.append(Paragraph(seg_text, normal_style))
                            
                            # Add details if available
                            details = segment.get('details', {})
                            if details:
                                for key, value in details.items():
                                    if value:
                                        detail_text = f"{key.replace('_', ' ').title()}: {value}"
                                        story.append(Paragraph(detail_text, normal_style))
                            story.append(Spacer(1, 0.1*inch))
                    
                    # Strategic Initiatives
                    elif section.get('type') == 'strategic_initiatives':
                        initiatives = section.get('initiatives', {})
                        for key, initiative in initiatives.items():
                            init_text = f"<b>{initiative.get('title', '')}</b><br/>"
                            if initiative.get('valuation'):
                                init_text += f"Valuation: {initiative.get('valuation', '')}<br/>"
                            if initiative.get('highlights'):
                                init_text += "Highlights:<br/>"
                                for highlight in initiative.get('highlights', []):
                                    init_text += f"• {highlight}<br/>"
                            story.append(Paragraph(init_text, normal_style))
                            story.append(Spacer(1, 0.1*inch))
                    
                    # Competitive Analysis
                    elif section.get('type') == 'competitive_analysis':
                        analysis = section.get('analysis', {})
                        for key, comp_data in analysis.items():
                            comp_text = f"<b>{comp_data.get('title', '')}</b><br/>"
                            # Add comparison data
                            for comp_key, comp_value in comp_data.items():
                                if comp_key != 'title' and comp_value:
                                    comp_text += f"{comp_key.replace('_', ' ').title()}: {comp_value}<br/>"
                            story.append(Paragraph(comp_text, normal_style))
                            story.append(Spacer(1, 0.1*inch))
                    
                    # Macro Context
                    elif section.get('type') == 'macro_context':
                        context = section.get('context', {})
                        for key, macro_data in context.items():
                            macro_text = f"<b>{macro_data.get('title', '')}</b><br/>"
                            # Add macro data
                            for macro_key, macro_value in macro_data.items():
                                if macro_key != 'title' and macro_value:
                                    if isinstance(macro_value, dict):
                                        for sub_key, sub_value in macro_value.items():
                                            macro_text += f"{sub_key.replace('_', ' ').title()}: {sub_value}<br/>"
                                    else:
                                        macro_text += f"{macro_key.replace('_', ' ').title()}: {macro_value}<br/>"
                            story.append(Paragraph(macro_text, normal_style))
                            story.append(Spacer(1, 0.1*inch))
                    
                    story.append(Spacer(1, 0.2*inch))
            
            # Chart Pattern Analysis
            chart_patterns = report_data.get('sections', {}).get('chart_patterns', {})
            if chart_patterns and chart_patterns.get('has_patterns'):
                story.append(Paragraph("Chart Pattern Analysis", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(chart_patterns.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                primary = chart_patterns.get('primary_pattern')
                if primary:
                    pattern_text = f"<b>Pattern:</b> {primary.get('pattern_name', 'N/A')}<br/>"
                    pattern_text += f"<b>Confidence:</b> {(primary.get('confidence', 0) * 100):.1f}%<br/>"
                    if primary.get('target_price'):
                        pattern_text += f"<b>Target Price:</b> ₹{primary.get('target_price', 0):.2f}<br/>"
                    if primary.get('potential_upside'):
                        pattern_text += f"<b>Potential Upside:</b> {primary.get('potential_upside', 0):.2f}%"
                    
                    story.append(Paragraph(pattern_text, normal_style))
                    story.append(Spacer(1, 0.3*inch))
            
            # Trading Analysis Sections
            sections = report_data.get('sections', {})
            
            # Trendline Analysis
            trendline_analysis = sections.get('trendline_analysis', {})
            if trendline_analysis and trendline_analysis.get('has_data'):
                story.append(Paragraph("Trendline Analysis", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(trendline_analysis.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                trendline_data = [['Metric', 'Value']]
                trendline_data.append(['Current Trend', trendline_analysis.get('current_trend', 'N/A').upper()])
                trendline_data.append(['Confidence', trendline_analysis.get('confidence', 'N/A')])
                trendline_data.append(['Uptrend Lines', str(trendline_analysis.get('uptrend_count', 0))])
                trendline_data.append(['Downtrend Lines', str(trendline_analysis.get('downtrend_count', 0))])
                trendline_data.append(['Channels', str(trendline_analysis.get('channel_count', 0))])
                trendline_data.append(['Recent Breaks', str(trendline_analysis.get('recent_breaks_count', 0))])
                
                trendline_table = Table(trendline_data, colWidths=[3*inch, 2*inch])
                trendline_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                ]))
                story.append(trendline_table)
                story.append(Spacer(1, 0.3*inch))
            
            # Market Structure Analysis
            market_structure = sections.get('market_structure_analysis', {})
            if market_structure and market_structure.get('has_data'):
                story.append(Paragraph("Market Structure Analysis", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(market_structure.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                structure_data = [['Metric', 'Value']]
                structure_data.append(['Current Phase', market_structure.get('current_phase', 'N/A').upper()])
                structure_data.append(['Structure Type', market_structure.get('structure_type', 'N/A')])
                structure_data.append(['BOS Events', str(market_structure.get('bos_count', 0))])
                structure_data.append(['CHoCH Events', str(market_structure.get('choch_count', 0))])
                
                structure_table = Table(structure_data, colWidths=[3*inch, 2*inch])
                structure_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                ]))
                story.append(structure_table)
                story.append(Spacer(1, 0.3*inch))
            
            # Support/Resistance Analysis
            support_resistance = sections.get('support_resistance_analysis', {})
            if support_resistance and support_resistance.get('has_data'):
                story.append(Paragraph("Support & Resistance Analysis", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(support_resistance.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                sr_data = [['Metric', 'Value']]
                sr_data.append(['Support Levels', str(support_resistance.get('support_levels_count', 0))])
                sr_data.append(['Resistance Levels', str(support_resistance.get('resistance_levels_count', 0))])
                sr_data.append(['Current Zone', support_resistance.get('current_zone', 'N/A').upper()])
                
                nearest_support = support_resistance.get('nearest_support')
                if nearest_support:
                    sr_data.append(['Nearest Support', f"₹{nearest_support.get('price', 0):.2f}"])
                
                nearest_resistance = support_resistance.get('nearest_resistance')
                if nearest_resistance:
                    sr_data.append(['Nearest Resistance', f"₹{nearest_resistance.get('price', 0):.2f}"])
                
                sr_table = Table(sr_data, colWidths=[3*inch, 2*inch])
                sr_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F59E0B')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                ]))
                story.append(sr_table)
                story.append(Spacer(1, 0.3*inch))
            
            # Swing Point Analysis
            swing_points = sections.get('swing_point_analysis', {})
            if swing_points and swing_points.get('has_data'):
                story.append(Paragraph("Swing Point Analysis", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(swing_points.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                swing_data = [['Metric', 'Value']]
                swing_data.append(['Swing Highs', str(swing_points.get('swing_highs_count', 0))])
                swing_data.append(['Swing Lows', str(swing_points.get('swing_lows_count', 0))])
                swing_data.append(['Trend', swing_points.get('trend', 'N/A').upper()])
                
                pattern_seq = swing_points.get('pattern_sequence', [])
                if pattern_seq:
                    swing_data.append(['Recent Pattern', ' → '.join(pattern_seq[-3:])])
                
                swing_table = Table(swing_data, colWidths=[3*inch, 2*inch])
                swing_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                ]))
                story.append(swing_table)
                story.append(Spacer(1, 0.3*inch))
            
            # Supply/Demand Analysis
            supply_demand = sections.get('supply_demand_analysis', {})
            if supply_demand and supply_demand.get('has_data'):
                story.append(Paragraph("Supply & Demand Analysis", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(supply_demand.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                sd_data = [['Metric', 'Value']]
                sd_data.append(['Demand Zones', str(supply_demand.get('demand_zones_count', 0))])
                sd_data.append(['Supply Zones', str(supply_demand.get('supply_zones_count', 0))])
                sd_data.append(['Fresh Demand Zones', str(supply_demand.get('fresh_demand_count', 0))])
                sd_data.append(['Fresh Supply Zones', str(supply_demand.get('fresh_supply_count', 0))])
                sd_data.append(['Tested Demand Zones', str(supply_demand.get('tested_demand_count', 0))])
                sd_data.append(['Tested Supply Zones', str(supply_demand.get('tested_supply_count', 0))])
                
                nearest_demand = supply_demand.get('nearest_demand')
                if nearest_demand:
                    price_range = nearest_demand.get('price_range', {})
                    sd_data.append(['Nearest Demand Zone', f"₹{price_range.get('low', 0):.2f} - ₹{price_range.get('high', 0):.2f}"])
                
                nearest_supply = supply_demand.get('nearest_supply')
                if nearest_supply:
                    price_range = nearest_supply.get('price_range', {})
                    sd_data.append(['Nearest Supply Zone', f"₹{price_range.get('low', 0):.2f} - ₹{price_range.get('high', 0):.2f}"])
                
                sd_table = Table(sd_data, colWidths=[3*inch, 2*inch])
                sd_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EC4899')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                ]))
                story.append(sd_table)
                story.append(Spacer(1, 0.3*inch))
            
            # Shared Chart Images Analysis
            chart_images = sections.get('chart_images_analysis', {})
            if chart_images and chart_images.get('has_data'):
                story.append(Paragraph("Shared Chart Images Analysis", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(chart_images.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                img_data = [['Metric', 'Value']]
                img_data.append(['Images Analyzed', str(chart_images.get('images_analyzed', 0))])
                img_data.append(['Patterns Detected', str(len(chart_images.get('detected_patterns', [])))])
                img_data.append(['Overall Trend', (chart_images.get('overall_trend', 'unknown') or 'unknown').upper()])
                img_data.append(['Key Levels', str(len(chart_images.get('key_levels', [])))])
                
                img_table = Table(img_data, colWidths=[3*inch, 2*inch])
                img_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366F1')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                ]))
                story.append(img_table)
                
                # Add detected patterns
                patterns = chart_images.get('detected_patterns', [])
                if patterns:
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph("Detected Patterns:", subheading_style))
                    for pattern in patterns[:5]:
                        pattern_text = f"<b>{pattern.get('pattern_name', 'Pattern')}</b> - "
                        pattern_text += f"Confidence: {(pattern.get('average_confidence', 0) * 100):.0f}%, "
                        pattern_text += f"Frequency: {pattern.get('frequency', 0)}"
                        story.append(Paragraph(pattern_text, normal_style))
                        story.append(Spacer(1, 0.05*inch))
                
                story.append(Spacer(1, 0.3*inch))
            
            # Market Factors Analysis
            market_factors = sections.get('market_factors', {})
            if market_factors and market_factors.get('has_data'):
                story.append(Paragraph("Market Factors Analysis", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(market_factors.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                # FII/DII Flows
                fii_dii = market_factors.get('fii_dii_flows', {})
                if fii_dii:
                    story.append(Paragraph("<b>Institutional Flows</b>", subheading_style))
                    fii_dii_data = [['Metric', 'Value']]
                    fii_net = fii_dii.get('fii_net_investment', 0)
                    dii_net = fii_dii.get('dii_net_investment', 0)
                    trend = fii_dii.get('trend', 'neutral')
                    data_source = fii_dii.get('data_source', 'Unknown')
                    
                    fii_dii_data.append(['FII Net Investment', f"₹{fii_net:.2f} Cr" if fii_net != 0 else "N/A"])
                    fii_dii_data.append(['DII Net Investment', f"₹{dii_net:.2f} Cr" if dii_net != 0 else "N/A"])
                    fii_dii_data.append(['Trend', trend.replace('_', ' ').title()])
                    fii_dii_data.append(['Data Source', data_source])
                    
                    fii_dii_table = Table(fii_dii_data, colWidths=[3*inch, 2*inch])
                    fii_dii_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7C3AED')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                    ]))
                    story.append(fii_dii_table)
                    story.append(Spacer(1, 0.2*inch))
                
                # Impact Analysis
                impact_analysis = market_factors.get('impact_analysis', {})
                if impact_analysis:
                    story.append(Paragraph("<b>Overall Impact Analysis</b>", subheading_style))
                    impact_data = [['Metric', 'Value']]
                    overall_impact = impact_analysis.get('overall_impact', 'Neutral')
                    impact_score = impact_analysis.get('impact_score', 0.0)
                    impact_summary = impact_analysis.get('summary', '')
                    
                    impact_data.append(['Overall Impact', overall_impact])
                    impact_data.append(['Impact Score', f"{impact_score:.2f}"])
                    impact_data.append(['Summary', impact_summary])
                    
                    # Add calculation explanation if available
                    calc_explanation = impact_analysis.get('calculation_explanation', {})
                    if calc_explanation:
                        method = calc_explanation.get('method', '')
                        interpretation = calc_explanation.get('interpretation', '')
                        impact_data.append(['Calculation Method', method])
                        impact_data.append(['Interpretation', interpretation])
                    
                    # Add detailed breakdown if available
                    detailed_breakdown = impact_analysis.get('detailed_breakdown', {})
                    if detailed_breakdown:
                        impact_data.append(['', ''])  # Empty row
                        impact_data.append(['<b>Factor Breakdown</b>', '<b>Score</b>'])
                        
                        if 'news' in detailed_breakdown:
                            news_breakdown = detailed_breakdown['news']
                            impact_data.append(['News Sentiment', f"{news_breakdown.get('score', 0):.2f} (Weight: {news_breakdown.get('weight', 'N/A')})"])
                        
                        if 'orderbook' in detailed_breakdown:
                            ob_breakdown = detailed_breakdown['orderbook']
                            impact_data.append(['Orderbook Pressure', f"{ob_breakdown.get('score', 0):.2f} (Weight: {ob_breakdown.get('weight', 'N/A')})"])
                        
                        if 'block_deals' in detailed_breakdown:
                            bd_breakdown = detailed_breakdown['block_deals']
                            impact_data.append(['Block Deals', f"{bd_breakdown.get('score', 0):.2f} (Weight: {bd_breakdown.get('weight', 'N/A')})"])
                        
                        if 'fii_dii' in detailed_breakdown:
                            fii_dii_breakdown = detailed_breakdown['fii_dii']
                            impact_data.append(['FII Investment', f"{fii_dii_breakdown.get('fii_score', 0):.2f} (Weight: {fii_dii_breakdown.get('fii_weight', 'N/A')})"])
                            impact_data.append(['DII Investment', f"{fii_dii_breakdown.get('dii_score', 0):.2f} (Weight: {fii_dii_breakdown.get('dii_weight', 'N/A')})"])
                    
                    impact_table = Table(impact_data, colWidths=[3*inch, 2*inch])
                    impact_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP')
                    ]))
                    story.append(impact_table)
                    story.append(Spacer(1, 0.3*inch))
            
            # Price Predictions
            price_predictions = sections.get('price_predictions', {})
            if price_predictions and price_predictions.get('has_data'):
                story.append(Paragraph("Price Predictions", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(price_predictions.get('summary', ''), normal_style))
                story.append(Spacer(1, 0.1*inch))
                
                current_price = price_predictions.get('current_price', 0)
                timeframes = price_predictions.get('timeframes', {})
                
                # Create predictions table
                pred_data = [['Timeframe', 'Predicted Price', 'Expected Return', 'Confidence', 'Risk Level']]
                
                for tf_name in ['1M', '2M', '3M', '6M']:
                    tf_data = timeframes.get(tf_name, {})
                    if tf_data:
                        predicted_price = tf_data.get('predicted_price', current_price)
                        expected_return = tf_data.get('expected_return', 0)
                        confidence = tf_data.get('confidence', 0)
                        risk_level = tf_data.get('risk_level', 'Medium')
                        
                        pred_data.append([
                            tf_name,
                            f"₹{predicted_price:.2f}",
                            f"{expected_return:+.2f}%",
                            f"{confidence:.0f}%",
                            risk_level
                        ])
                
                if len(pred_data) > 1:
                    pred_table = Table(pred_data, colWidths=[1*inch, 1.5*inch, 1.2*inch, 1*inch, 1*inch])
                    pred_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                    ]))
                    story.append(pred_table)
                    story.append(Spacer(1, 0.2*inch))
                
                # Add detailed predictions with price ranges
                story.append(Paragraph("<b>Detailed Predictions</b>", subheading_style))
                for tf_name in ['1M', '2M', '3M', '6M']:
                    tf_data = timeframes.get(tf_name, {})
                    if tf_data:
                        predicted_price = tf_data.get('predicted_price', current_price)
                        price_range = tf_data.get('price_range', {})
                        change_percent = tf_data.get('potential_change_percent', 0)
                        confidence = tf_data.get('confidence', 0)
                        
                        pred_text = f"<b>{tf_name} ({tf_data.get('days', 0)} days):</b> "
                        pred_text += f"Predicted Price: ₹{predicted_price:.2f} "
                        pred_text += f"({change_percent:+.1f}% from current ₹{current_price:.2f})<br/>"
                        pred_text += f"Confidence: {confidence:.0f}% | "
                        
                        if price_range:
                            pred_text += f"Price Range (68%): ₹{price_range.get('low_68', 0):.2f} - ₹{price_range.get('high_68', 0):.2f}<br/>"
                            pred_text += f"Price Range (95%): ₹{price_range.get('low_95', 0):.2f} - ₹{price_range.get('high_95', 0):.2f}"
                        
                        story.append(Paragraph(pred_text, normal_style))
                        story.append(Spacer(1, 0.1*inch))
                
                # Add contributing factors
                first_tf = timeframes.get('1M', {})
                if first_tf:
                    factors = first_tf.get('factors_contributing', [])
                    if factors:
                        story.append(Spacer(1, 0.1*inch))
                        story.append(Paragraph("<b>Key Contributing Factors:</b>", subheading_style))
                        for factor in factors[:5]:  # Top 5 factors
                            factor_text = f"• {factor.get('factor', '')}: {factor.get('direction', 'neutral').title()} "
                            factor_text += f"(Contribution: {factor.get('contribution', 0):.3f})"
                            story.append(Paragraph(factor_text, normal_style))
                        story.append(Spacer(1, 0.1*inch))
                
                story.append(Spacer(1, 0.3*inch))
            
            # 10 Strong Points
            strong_points = report_data.get('sections', {}).get('strong_points', {})
            if strong_points and strong_points.get('count', 0) > 0:
                story.append(Paragraph(f"{strong_points.get('count', 0)} Strong Points", heading_style))
                story.append(Spacer(1, 0.1*inch))
                
                points = strong_points.get('points', [])
                for idx, point in enumerate(points[:10], 1):
                    point_text = f"<b>{idx}. {point.get('point', '')}</b><br/>{point.get('description', '')}"
                    story.append(Paragraph(point_text, normal_style))
                    story.append(Spacer(1, 0.1*inch))
                
                story.append(Spacer(1, 0.2*inch))
            
            # Conclusion
            conclusion = report_data.get('sections', {}).get('conclusion', {})
            if conclusion:
                story.append(PageBreak())
                story.append(Paragraph("Conclusion", heading_style))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(conclusion.get('summary', ''), normal_style))
            
            # Build PDF
            doc.build(story)
            
            if output_path:
                logger.info(f"PDF saved to {output_path}")
                return BytesIO()
            else:
                buffer.seek(0)
                return buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise

# Create singleton instance
research_report_pdf_generator = ResearchReportPDFGenerator()

