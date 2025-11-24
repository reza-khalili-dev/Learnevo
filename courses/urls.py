from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [

    # -------------------------------
    # Dashboard
    # -------------------------------
    path('dashboard/', views.CoursesDashboardView.as_view(), name='dashboard'),

    # -------------------------------
    # Courses CRUD
    # -------------------------------
    path('', views.CourseListView.as_view(), name='course_list'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('create/', views.CourseCreateView.as_view(), name='course_create'),
    path('<int:pk>/update/', views.CourseUpdateView.as_view(), name='course_update'),
    path('<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),

    # -------------------------------
    # Classes CRUD
    # -------------------------------
    path('classes/', views.ClassListView.as_view(), name='class_list'),
    path('classes/create/', views.ClassCreateView.as_view(), name='class_create'),
    path('classes/<int:pk>/', views.ClassDetailView.as_view(), name='class_detail'),
    path('classes/<int:pk>/update/', views.ClassUpdateView.as_view(), name='class_update'),
    path('classes/<int:pk>/delete/', views.ClassDeleteView.as_view(), name='class_delete'),

    # -------------------------------
    # Sessions CRUD
    # -------------------------------
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('classroom/<int:classroom_id>/sessions/create/', views.SessionCreateView.as_view(), name='session_create'),
    path('sessions/<int:pk>/update/', views.SessionUpdateView.as_view(), name='session_update'),
    path('sessions/<int:pk>/delete/', views.SessionDeleteView.as_view(), name='session_delete'),

    # -------------------------------
    # Assignments CRUD
    # -------------------------------
    path('courses/<int:course_pk>/assignments/', views.AssignmentListView.as_view(), name='assignment_list'),
    path('assignments/<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    path('courses/<int:course_pk>/assignments/create/', views.AssignmentCreateView.as_view(), name='assignment_create'),
    path('assignments/<int:pk>/update/', views.AssignmentUpdateView.as_view(), name='assignment_update'),
    path('assignments/<int:pk>/delete/', views.AssignmentDeleteView.as_view(), name='assignment_delete'),

    # -------------------------------
    # Submissions
    # -------------------------------
    path('assignments/<int:assignment_pk>/submissions/', views.SubmissionListView.as_view(), name='submission_list'),
    path('assignments/<int:assignment_pk>/submit/', views.SubmissionCreateView.as_view(), name='submission_create'),
    path('submissions/<int:pk>/', views.SubmissionUpdateView.as_view(), name='submission_update'),

    # -------------------------------
    # Instructor Views
    # -------------------------------
    path('instructor/courses/', views.InstructorCourseListView.as_view(), name='instructor_courses'),
    path('instructor/sessions/', views.InstructorSessionListView.as_view(), name='instructor_sessions'),

    # -------------------------------
    # Attendance System
    # -------------------------------
    path('attendances/classroom/<int:classroom_pk>/',views.ClassroomAttendanceView.as_view(),name='classroom_attendance'),
    path("classes/<int:classroom_pk>/attendance/save/", views.AttendanceSaveView.as_view(), name="attendance_save"),

    # -------------------------------
    # Attendance REPORTS
    # -------------------------------
    path("reports/", views.ReportsDashboardView.as_view(), name="reports_dashboard"),
    path("reports/class/<int:class_id>/", views.ReportClassView.as_view(), name="report_class"),
    path("reports/class/<int:class_id>/pdf/", views.ReportClassPDFView.as_view(), name="report_class_pdf"),
    path("reports/session/<int:session_id>/", views.ReportSessionView.as_view(), name="report_session"),
    path("reports/session/<int:session_id>/pdf/", views.ReportSessionPDFView.as_view(), name="report_session_pdf"),
    ]
