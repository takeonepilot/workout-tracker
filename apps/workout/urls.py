from django.urls import path
from . import views

urlpatterns = [
    # User Management
    path("", views.login, name="login"),  # Index / Login page
    path("user/register", views.register, name="register"),  # Register user
    path("user/login", views.login, name="login_user"),  # Log in existing user
    path("user/logout", views.logout, name="logout"),  # Log out user
    # Dashboard
    path("dashboard", views.dashboard, name="dashboard"),  # Dashboard view
    # Workout Management
    path("workout", views.new_workout, name="new_workout"),  # Add new workout
    path("workouts", views.all_workouts, name="all_workouts"),  # View all workouts
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
    path("workout/session/<int:id>/", views.view_session, name="view_session"),
    path("workout/next-session", views.next_session, name="next_session"),
    path("history", views.session_history, name="history"),  # View session history
    # Update Exercise Session - Adicionando a rota para atualizar os detalhes do exercício
    path(
        "session/<int:id>/exercise/<int:exercise_id>/update/",
        views.update_exercise_session,
        name="update_exercise_session",
    ),
    # apps/workout/urls.py
    path(
        "workout/plan/<int:plan_id>/reorder/",
        views.reorder_workouts,
        name="reorder_workouts",
    ),
    # User Settings
    path("settings", views.settings, name="settings"),  # User settings
    # Legal and Terms
    path("legal/tos", views.tos, name="tos"),  # Terms of Service
]
