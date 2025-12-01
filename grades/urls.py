from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    # ========== Grade URLs ==========
    path('', views.GradeListView.as_view(), name='grade_list'),
    path('<int:pk>/', views.GradeDetailView.as_view(), name='grade_detail'),
    path('create/', views.GradeCreateView.as_view(), name='grade_create'),
    path('<int:pk>/update/', views.GradeUpdateView.as_view(), name='grade_update'),
    path('<int:pk>/delete/', views.GradeDeleteView.as_view(), name='grade_delete'),
    
    # assignment
    path('submission/<int:submission_pk>/grade/', 
         views.AssignmentGradeCreateView.as_view(), 
         name='assignment_grade_create'),
    
    # BulkGrade
    path('bulk-publish/', views.BulkGradePublishView.as_view(), name='bulk_grade_publish'),
    
    # ========== Report Card URLs ==========
    path('report-cards/', views.ReportCardListView.as_view(), name='reportcard_list'),
    path('report-cards/<int:pk>/', views.ReportCardDetailView.as_view(), name='reportcard_detail'),
    path('report-cards/create/', views.ReportCardCreateView.as_view(), name='reportcard_create'),
    path('report-cards/<int:pk>/publish/', 
         views.ReportCardPublishView.as_view(), 
         name='reportcard_publish'),
    path('report-cards/<int:pk>/pdf/', 
         views.ReportCardPDFView.as_view(), 
         name='reportcard_pdf'),
    
    # ========== Dashboard & Student Views ==========
    path('dashboard/', views.GradesDashboardView.as_view(), name='dashboard'),
    path('student/<int:student_id>/', views.StudentGradesView.as_view(), name='student_grades'),
    
    # ========== API URLs ==========
    path('api/statistics/', views.GradeStatisticsAPIView.as_view(), name='grade_statistics_api'),
    
    # ========== Grading Scale URLs ==========
    path('scales/', views.GradingScaleListView.as_view(), name='gradingscale_list'),
    path('scales/create/', views.GradingScaleCreateView.as_view(), name='gradingscale_create'),
    path('scales/<int:pk>/update/', views.GradingScaleUpdateView.as_view(), name='gradingscale_update'),
    path('scales/<int:pk>/delete/', views.GradingScaleDeleteView.as_view(), name='gradingscale_delete'),
]