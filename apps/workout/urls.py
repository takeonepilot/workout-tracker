from django.urls import path
from . import views

urlpatterns = [
    # Root URL ("/") - redirect to login
    path("", views.login, name="root"),  # Root page redirects to login
    # User Management
    path("user/login", views.login, name="login"),  # Login page
    path("user/register", views.register, name="register"),  # Register user
    path("user/logout", views.logout, name="logout"),  # Log out user
    # Dashboard
    path("dashboard", views.dashboard, name="dashboard"),  # Dashboard view
    # Workout Management
    path("workout", views.new_workout, name="new_workout"),  # Add new workout
    path("workouts", views.all_workouts, name="all_workouts"),  # View all
    path("workout/<int:id>/", views.workout, name="view_workout"),  # View a workout
    path(
        "workout/<int:id>/exercise", views.exercise, name="add_exercise"
    ),  # Add exercise to workout
    path(
        "workout/<int:id>/complete", views.complete_workout, name="complete_workout"
    ),  # Complete workout
    path(
        "workout/<int:id>/edit", views.edit_workout, name="edit_workout"
    ),  # Edit workout
    path(
        "workout/<int:id>/delete", views.delete_workout, name="delete_workout"
    ),  # Delete workout
    # Workout Sessions
    path(
        "workout/session/<int:id>/", views.view_session, name="view_session"
    ),  # View session details
    path("workout/session/current", views.current_session, name="current_session"),
    path(
        "workout/<int:workout_id>/start-session/",
        views.start_workout_session,
        name="start_workout_session",
    ),
    path("history", views.session_history, name="session_history"),
    path(
        "workout/history/<int:id>/",
        views.view_history_session,
        name="view_history_session",
    ),  # Add new route for viewing session history details
    # Import Workouts via Spreadsheet
    path(
        "workouts/import", views.importar_treinos, name="importar_treinos"
    ),  # Import workouts from Excel file
    # User Settings
    path("settings", views.settings, name="settings"),  # User settings
    # Legal and Terms
    path("legal/tos", views.tos, name="tos"),  # Terms of Service
]
