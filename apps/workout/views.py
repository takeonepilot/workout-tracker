from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.http import HttpResponse
from django.utils import timezone
from .models import User, Workout, Exercise, WorkoutSession, ExerciseSession
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


# Função auxiliar para obter o usuário logado
def get_logged_in_user(request):
    try:
        user = User.objects.get(id=request.session["user_id"])
        return user
    except (KeyError, User.DoesNotExist):
        messages.info(
            request,
            "Você precisa estar logado para acessar esta página.",
            extra_tags="invalid_session",
        )
        return None


def login(request):
    # Verificar se o usuário já está autenticado antes de exibir a página de login.
    if request.user.is_authenticated:
        return redirect(
            "/dashboard"
        )  # Redireciona para o dashboard se o usuário já estiver autenticado.

    if request.method == "GET":
        return render(request, "workout/index.html")

    if request.method == "POST":
        # Valida o login (certifique-se de que a função login no modelo User funciona corretamente).
        validated = User.objects.login(**request.POST)
        if "errors" in validated:
            for error in validated["errors"]:
                messages.error(request, error, extra_tags="login")
            return redirect("/")  # Redireciona para a página de login em caso de erro.
        else:
            # Loga o usuário e redireciona para o dashboard.
            user = validated["logged_in_user"]
            auth_login(
                request, user
            )  # Faz login do usuário usando o sistema de autenticação do Django.
            return redirect("/dashboard")


def register(request):
    if request.method == "GET":
        return render(request, "workout/register.html")

    if request.method == "POST":
        validated = User.objects.register(**request.POST)
        if "errors" in validated:
            for error in validated["errors"]:
                messages.error(request, error, extra_tags="registration")
            return redirect("/user/register")
        else:
            request.session["user_id"] = validated["logged_in_user"].id
            return redirect("/dashboard")


def logout(request):
    request.session.flush()
    messages.success(request, "Você foi desconectado.", extra_tags="logout")
    return redirect("/")


def dashboard(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    recent_workouts = Workout.objects.filter(user=user).order_by("-id")[:4]
    context = {
        "user": user,
        "recent_workouts": recent_workouts,
    }
    return render(request, "workout/dashboard.html", context)


def new_workout(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    if request.method == "GET":
        return render(request, "workout/add_workout.html", {"user": user})

    if request.method == "POST":
        workout_data = {
            "name": request.POST["name"],
            "description": request.POST["description"],
            "user": user,
        }
        validated = Workout.objects.new(**workout_data)
        if "errors" in validated:
            for error in validated["errors"]:
                messages.error(request, error, extra_tags="workout")
            return redirect("/workout")
        return redirect(f'/workout/{validated["workout"].id}')


def workout(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    workout_instance = get_object_or_404(Workout, id=id, user=user)
    exercises = Exercise.objects.filter(workout=workout_instance).order_by(
        "-updated_at"
    )

    context = {
        "user": user,
        "workout": workout_instance,
        "exercises": exercises,
    }
    return render(request, "workout/workout.html", context)


def all_workouts(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    workout_list = Workout.objects.filter(user=user).order_by("-id")
    page = request.GET.get("page", 1)
    paginator = Paginator(workout_list, 12)
    try:
        workouts = paginator.page(page)
    except PageNotAnInteger:
        workouts = paginator.page(1)
    except EmptyPage:
        workouts = paginator.page(paginator.num_pages)

    context = {
        "user": user,
        "workouts": workouts,
    }
    return render(request, "workout/all_workouts.html", context)


def exercise(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    workout_instance = get_object_or_404(Workout, id=id, user=user)

    # Se o método for GET e houver um 'exercise_id', exclui o exercício
    if request.method == "GET" and "exercise_id" in request.GET:
        Exercise.objects.filter(id=request.GET["exercise_id"]).delete()
        return redirect(f"/workout/{id}")

    # Se o método for POST, tenta criar um novo exercício
    if request.method == "POST":
        exercise_data = {
            "name": request.POST["name"],
            "repetitions": request.POST["repetitions"],
            "rpe": request.POST.get("rpe"),
            "sets": request.POST.get("sets", 1),
            "workout": workout_instance,
        }

        # Criação do novo exercício sem esperar o campo 'weight'
        validated = Exercise.objects.new(**exercise_data)
        if "errors" in validated:
            for error in validated["errors"]:
                messages.error(request, error, extra_tags="exercise")
        return redirect(f"/workout/{id}")


def edit_workout(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    workout_instance = get_object_or_404(Workout, id=id, user=user)

    if request.method == "GET":
        exercises = Exercise.objects.filter(workout=workout_instance)
        context = {
            "user": user,
            "workout": workout_instance,
            "exercises": exercises,
        }
        return render(request, "workout/edit_workout.html", context)

    if request.method == "POST":
        workout_data = {
            "name": request.POST["name"],
            "description": request.POST["description"],
            "workout_id": workout_instance.id,
        }
        validated = Workout.objects.update(**workout_data)
        if "errors" in validated:
            for error in validated["errors"]:
                messages.error(request, error, extra_tags="edit")
            return redirect(f"/workout/{id}/edit")
        return redirect(f"/workout/{id}")


def delete_workout(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    workout_instance = get_object_or_404(Workout, id=id, user=user)

    if request.method == "POST":
        workout_instance.delete()
        messages.success(request, "Treino excluído com sucesso.")
        return redirect("/workouts")


def complete_workout(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    workout_instance = get_object_or_404(Workout, id=id, user=user)

    if request.method == "POST":
        workout_instance.completed = True
        workout_instance.save()
        messages.success(request, "Treino concluído com sucesso.")
        return redirect(f"/workout/{id}")


def view_session(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    # Obtém a sessão do treino e garante que pertence ao usuário logado
    session = get_object_or_404(WorkoutSession, id=id, user=user)
    exercises = ExerciseSession.objects.filter(workout_session=session)

    # Verifica se há exercícios na sessão
    if not exercises.exists():
        messages.info(request, "Nenhum exercício encontrado para esta sessão.")

    context = {
        "user": user,
        "session": session,
        "exercises": exercises,
    }
    return render(request, "workout/view_session.html", context)


def next_session(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    # Busca a próxima sessão com base na data atual
    next_session = (
        WorkoutSession.objects.filter(user=user, date__gt=timezone.now())
        .order_by("date")
        .first()
    )

    # Verifica se há uma próxima sessão
    if not next_session:
        messages.info(
            request,
            "Você não tem nenhuma próxima sessão de treino agendada. Crie um novo treino para começar.",
        )
        return redirect("/workout")  # Redireciona para a criação de um novo treino

    # Redireciona diretamente para a página da próxima sessão encontrada
    return redirect("view_session", id=next_session.id)


def session_history(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    sessions = WorkoutSession.objects.filter(user=user).order_by("-date")
    context = {
        "user": user,
        "sessions": sessions,
    }
    return render(request, "workout/session_history.html", context)


def settings(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    if request.method == "GET":
        return render(request, "workout/settings.html", {"user": user})

    if request.method == "POST":
        user.username = request.POST.get("username", user.username)
        user.email = request.POST.get("email", user.email)
        password = request.POST.get("password")
        password_confirmation = request.POST.get("password_confirmation")

        if password and password == password_confirmation:
            user.set_password(password)
        user.save()

        messages.success(request, "Configurações atualizadas com sucesso.")
        return redirect("/settings")


def tos(request):
    return render(request, "workout/legal/tos.html")
