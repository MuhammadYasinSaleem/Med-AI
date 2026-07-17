"""
Django admin customization for Lab Report Analyzer.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json


from .models import Patient, LabReport, AnalysisResult


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Admin interface for Patient model."""
    
    list_display = ['name', 'age', 'gender', 'is_pregnant', 'contact', 'created_at', 'lab_reports_count']
    list_filter = ['gender', 'is_pregnant', 'created_at']
    search_fields = ['name', 'contact']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def lab_reports_count(self, obj):
        """Display count of lab reports for this patient."""
        count = obj.lab_reports.count()
        if count > 0:
            url = reverse('admin:lab_analyzer_labreport_changelist')
            return format_html('<a href="{}?patient__id__exact={}">{} reports</a>', url, obj.id, count)
        return '0 reports'
    lab_reports_count.short_description = 'Lab Reports'


@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    """Admin interface for LabReport model."""
    
    list_display = [
        'id_short', 'patient_link', 'original_filename', 'status_badge',
        'has_analysis', 'critical_flag', 'uploaded_at', 'processed_at'
    ]
    list_filter = ['status', 'uploaded_at', 'analysis_result__has_critical']
    search_fields = ['patient__name', 'original_filename', 'id']
    readonly_fields = [
        'id', 'uploaded_at', 'processed_at', 'file_preview',
        'analysis_link', 'file_info'
    ]
    date_hierarchy = 'uploaded_at'
    actions = ['reprocess_reports', 'export_as_json']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('id', 'patient', 'original_filename', 'file', 'file_info', 'file_preview')
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'uploaded_at', 'processed_at')
        }),
        ('Analysis', {
            'fields': ('analysis_link',)
        }),
    )
    
    def id_short(self, obj):
        """Display shortened UUID."""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def patient_link(self, obj):
        """Link to patient admin page."""
        url = reverse('admin:lab_analyzer_patient_change', args=[obj.patient.id])
        return format_html('<a href="{}">{}</a>', url, obj.patient.name)
    patient_link.short_description = 'Patient'
    
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'pending': 'gray',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_analysis(self, obj):
        """Check if analysis exists."""
        return hasattr(obj, 'analysis_result')
    has_analysis.boolean = True
    has_analysis.short_description = 'Has Analysis'
    
    def critical_flag(self, obj):
        """Display critical flag if exists."""
        if hasattr(obj, 'analysis_result') and obj.analysis_result.has_critical:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">CRITICAL</span>'
            )
        return '-'
    critical_flag.short_description = 'Critical'
    
    def file_preview(self, obj):
        """Preview file link."""
        if obj.file:
            return format_html('<a href="{}" target="_blank">View File</a>', obj.file.url)
        return '-'
    file_preview.short_description = 'File Preview'
    
    def file_info(self, obj):
        """Display file information."""
        if obj.file:
            ext = obj.get_file_extension()
            size = obj.file.size / 1024  # KB
            return f"Type: {ext.upper()}, Size: {size:.2f} KB"
        return '-'
    file_info.short_description = 'File Info'
    
    def analysis_link(self, obj):
        """Link to analysis result."""
        if hasattr(obj, 'analysis_result'):
            url = reverse('admin:lab_analyzer_analysisresult_change', args=[obj.analysis_result.id])
            return format_html('<a href="{}">View Analysis</a>', url)
        return 'No analysis yet'
    analysis_link.short_description = 'Analysis'
    
    def reprocess_reports(self, request, queryset):
        """Action to reprocess selected reports."""
        from .tasks import process_lab_report
        
        count = 0
        for report in queryset.filter(status__in=['failed', 'completed']):
            report.status = 'pending'
            report.error_message = ''
            report.save()
            process_lab_report.delay(str(report.id))
            count += 1
        
        self.message_user(request, f'{count} report(s) queued for reprocessing.')
    reprocess_reports.short_description = 'Reprocess selected reports'
    
    def export_as_json(self, request, queryset):
        """Export selected reports as JSON."""
        import json
        from django.http import HttpResponse
        
        data = []
        for report in queryset:
            report_data = {
                'id': str(report.id),
                'patient': {
                    'name': report.patient.name,
                    'age': report.patient.age,
                    'gender': report.patient.gender,
                },
                'filename': report.original_filename,
                'status': report.status,
                'uploaded_at': report.uploaded_at.isoformat(),
            }
            if hasattr(report, 'analysis_result'):
                report_data['analysis'] = report.analysis_result.findings
            
            data.append(report_data)
        
        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="lab_reports_export.json"'
        return response
    export_as_json.short_description = 'Export selected as JSON'


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    """Admin interface for AnalysisResult model."""
    
    list_display = [
        'id_short', 'lab_report_link', 'patient_name', 'critical_flags',
        'has_critical_badge', 'processing_time', 'generated_at'
    ]
    list_filter = ['has_critical', 'generated_at']
    search_fields = ['lab_report__patient__name', 'lab_report__id']
    readonly_fields = [
        'id', 'lab_report', 'findings_display', 'clinical_summary',
        'critical_flags', 'has_critical', 'generated_at', 'processing_time'
    ]
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'lab_report', 'generated_at', 'processing_time')
        }),
        ('Findings Summary', {
            'fields': ('critical_flags', 'has_critical', 'clinical_summary')
        }),
        ('Detailed Findings', {
            'fields': ('findings_display',),
            'classes': ('collapse',)
        }),
    )
    
    def id_short(self, obj):
        """Display shortened UUID."""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def lab_report_link(self, obj):
        """Link to lab report admin page."""
        url = reverse('admin:lab_analyzer_labreport_change', args=[obj.lab_report.id])
        return format_html('<a href="{}">Report {}</a>', url, str(obj.lab_report.id)[:8])
    lab_report_link.short_description = 'Lab Report'
    
    def patient_name(self, obj):
        """Display patient name."""
        return obj.lab_report.patient.name
    patient_name.short_description = 'Patient'
    
    def has_critical_badge(self, obj):
        """Display critical badge."""
        if obj.has_critical:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">CRITICAL</span>'
            )
        return format_html('<span style="color: green;">Normal</span>')
    has_critical_badge.short_description = 'Status'
    
    def findings_display(self, obj):
        """Display findings as formatted JSON."""
        return format_html(
            '<pre style="max-height: 500px; overflow: auto;">{}</pre>',
            json.dumps(obj.findings, indent=2)
        )
    findings_display.short_description = 'Findings (JSON)'
