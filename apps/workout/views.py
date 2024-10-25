# apps\workout\views.py

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from .models import *

import pandas as pd


# Funções de Login, Registro, Logout, Dashboard e Configurações de Usuário
def get_logged_in_user(request):
    if request.user.is_authenticated:
        return request.user
    else:
        messages.info(
            request,
            "Você precisa estar logado para acessar esta página.",
            extra_tags="invalid_session",
        )
        return None


def login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "GET":
        return render(request, "workout/index.html")

    if request.method == "POST":
        validated = User.objects.login(**request.POST)
        if "errors" in validated:
            for error in validated["errors"]:
                messages.error(request, error, extra_tags="login")
            return redirect("login")

        user = validated["logged_in_user"]
        auth_login(request, user)
        return redirect("dashboard")


def register(request):
    if request.method == "GET":
        return render(request, "workout/register.html")
    if request.method == "POST":
        validated = User.objects.register(**request.POST)
        if "errors" in validated:
            for error in validated["errors"]:
                messages.error(request, error, extra_tags="registration")
            return redirect("/user/register")
        request.session["user_id"] = validated["logged_in_user"].id
        return redirect("/dashboard")


def logout(request):
    auth_logout(request)
    messages.success(request, "Você foi desconectado.", extra_tags="logout")
    return redirect("login")


def dashboard(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect(
            "login"
        )  # Redireciona para o login se o usuário não estiver logado

    recent_workouts = Workout.objects.filter(user=user).order_by("-id")[:4]
    context = {"user": user, "recent_workouts": recent_workouts}
    return render(request, "workout/dashboard.html", context)


# Configurações de Usuário
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


# Gerenciamento de Treinos
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
            "order_id": int(request.POST["order_id"]),
            "user": user,
        }
        validated = Workout.objects.create_workout(**workout_data)
        if "errors" in validated:
            for error in validated["errors"]:
                messages.error(request, error, extra_tags="workout")
            return redirect("/workout")

        return redirect(f'/workout/{validated["workout"].id}')


def edit_workout(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")
    workout_instance = get_object_or_404(Workout, id=id, user=user)

    if request.method == "GET":
        exercises = Exercise.objects.filter(workout=workout_instance)
        context = {"user": user, "workout": workout_instance, "exercises": exercises}
        return render(request, "workout/edit_workout.html", context)

    if request.method == "POST":
        workout_instance.name = request.POST["name"]
        workout_instance.description = request.POST["description"]
        workout_instance.order_id = int(request.POST["order_id"])  # Ajustando a ordem
        workout_instance.save()
        messages.success(request, "Treino atualizado com sucesso.")
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


def workout(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")
    workout_instance = get_object_or_404(Workout, id=id, user=user)
    exercises = Exercise.objects.filter(workout=workout_instance).order_by(
        "-updated_at"
    )
    context = {"user": user, "workout": workout_instance, "exercises": exercises}
    return render(request, "workout/workout.html", context)


def exercise(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    workout_instance = get_object_or_404(Workout, id=id, user=user)

    if request.method == "POST":
        exercise_data = {
            "name": request.POST["name"],
            "repetitions": request.POST["repetitions"],
            "rpe": request.POST.get("rpe"),
            "sets": request.POST.get("sets", 1),
            "workout": workout_instance,
        }
        validated = Exercise.objects.create_exercise(**exercise_data)
        if "errors" in validated:
            for error in validated["errors"]:
                messages.error(request, error, extra_tags="exercise")
        return redirect(f"/workout/{id}")


def all_workouts(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    workout_list = Workout.objects.filter(user=user).order_by("order_id")
    page = request.GET.get("page", 1)
    paginator = Paginator(workout_list, 12)

    try:
        workouts = paginator.page(page)
    except PageNotAnInteger:
        workouts = paginator.page(1)
    except EmptyPage:
        workouts = paginator.page(paginator.num_pages)

    context = {"user": user, "workouts": workouts}
    return render(request, "workout/all_workouts.html", context)


def start_workout_session(request, workout_id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    workout = get_object_or_404(Workout, id=workout_id, user=user)
    workout_session = WorkoutSession.objects.create(workout=workout, user=user)

    try:
        # Adiciona log para verificar se a função está sendo chamada
        print(
            f"Iniciando a criação de ExerciseSessions para a sessão de treino: {workout_session.id}"
        )

        # Verifica se a criação das ExerciseSession está no lugar certo
        workout_session.create_exercise_sessions()  # Cria as sessões de exercícios
        messages.success(request, "Sessão de treino iniciada com sucesso.")
    except Exception as e:
        print(f"Erro ao criar as sessões de exercício: {e}")
        messages.error(request, "Erro ao iniciar a sessão de treino. Tente novamente.")
        return redirect("dashboard")

    return redirect("view_session", id=workout_session.id)


def create_exercise_sessions(self):
    """Método para criar ExerciseSession ao iniciar uma WorkoutSession."""
    exercises = self.workout.exercise_set.all()  # Obtenha todos os exercícios do treino

    if not exercises:
        print(f"Não foram encontrados exercícios para o treino: {self.workout.name}")
        return  # Se não houver exercícios, retorne sem criar

    print(f"Exercícios encontrados para o treino {self.workout.name}: {exercises}")

    for exercise in exercises:
        try:
            # Cria uma ExerciseSession para cada exercício no treino
            ExerciseSession.objects.create(
                workout_session=self,
                exercise=exercise,
                weight_used=0,  # Valor padrão inicial
                actual_repetitions=0,
                sets=exercise.sets,
                rpe=exercise.rpe,
            )
            print(f"ExerciseSession criado para o exercício: {exercise.name}")
        except Exception as e:
            print(f"Erro ao criar ExerciseSession para {exercise.name}: {e}")


def complete_workout(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    # Buscar o treino e seus exercícios
    workout_instance = get_object_or_404(Workout, id=id, user=user)
    exercises = Exercise.objects.filter(workout=workout_instance)

    if request.method == "POST":
        # Criar uma nova sessão de treino (WorkoutSession)
        workout_session = WorkoutSession.objects.create(
            user=user,
            workout=workout_instance,
            date=timezone.now(),
            completed=True,  # Marcar a sessão como concluída
        )

        # Marcar o treino (Workout) como concluído
        workout_instance.completed = True
        workout_instance.save()

        # Criar uma instância de WorkoutHistory
        workout_history = WorkoutHistory.objects.create(
            workout=workout_instance,
            user=user,
            completed=True,
            date=timezone.now(),
        )

        # Criar um histórico de exercícios para cada exercício do treino
        for exercise in exercises:
            for i in range(1, exercise.sets + 1):  # Loop sobre as séries
                weight_key = f"weight_{exercise.id}_{i}"
                reps_key = f"repetitions_{exercise.id}_{i}"

                weight_used = request.POST.get(weight_key, 0)  # Pega o valor do peso
                actual_repetitions = request.POST.get(
                    reps_key, 0
                )  # Pega o valor das repetições

                # Criar um histórico de exercícios para cada série
                ExerciseHistory.objects.create(
                    workout_history=workout_history,  # Relacionar ao histórico de treino
                    exercise=exercise,
                    weight_used=weight_used,
                    actual_repetitions=actual_repetitions,
                    sets=exercise.sets,
                    rpe=exercise.rpe,
                )

        messages.success(
            request, "Treino concluído com sucesso e registrado no histórico."
        )
        return redirect("session_history")

    context = {"user": user, "workout": workout_instance, "exercises": exercises}
    return render(request, "workout/session_history.html", context)


def view_session(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    # Buscar a sessão de treino (WorkoutSession) pelo ID e pelo usuário
    session = get_object_or_404(WorkoutSession, id=id, user=user)

    # Buscar as ExerciseSession associadas a essa sessão de treino
    exercises = ExerciseSession.objects.filter(workout_session=session)

    # Se nenhuma ExerciseSession foi encontrada, criá-las
    if not exercises.exists():
        session.create_exercise_sessions()
        # Após criar, busque novamente as ExerciseSession
        exercises = ExerciseSession.objects.filter(workout_session=session)

    exercises_with_series = []
    for exercise in exercises:
        # Certifique-se de que estamos recuperando as informações de séries corretamente
        exercises_with_series.append(
            {
                "exercise": exercise,
                "series": exercise.series.all(),  # Certifique-se de que as séries estão sendo recuperadas corretamente
                "series_range": range(1, exercise.sets + 1),  # Gera a faixa de séries
            }
        )

    # Verificação do envio do formulário para salvar as séries
    if request.method == "POST":
        for exercise_session in exercises:
            for i in range(1, exercise_session.sets + 1):
                weight = request.POST.get(
                    f"weight_{exercise_session.exercise.id}_{i}", 0
                )
                repetitions = request.POST.get(
                    f"repetitions_{exercise_session.exercise.id}_{i}", 0
                )

                # Atualizar o peso e as repetições usados
                weight = float(weight) if weight else 0
                repetitions = int(repetitions) if repetitions else 0

                # Atualiza a session com os valores inseridos
                exercise_session.weight_used = weight
                exercise_session.actual_repetitions = repetitions
                exercise_session.save()

        messages.success(request, "Sessão de treino atualizada com sucesso.")
        return redirect("view_session", id=session.id)

    context = {
        "user": user,
        "session": session,
        "exercises_with_series": exercises_with_series,
    }
    return render(request, "workout/view_session.html", context)


def session_history(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    sessions = WorkoutSession.objects.filter(user=user, completed=True).order_by(
        "-date"
    )

    context = {"user": user, "sessions": sessions}
    return render(request, "workout/session_history.html", context)


def view_history_session(request, id):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    # Buscar a sessão de treino (WorkoutSession) pelo ID e pelo usuário
    session = get_object_or_404(WorkoutSession, id=id, user=user)

    # Buscar os ExerciseHistory associados a essa sessão de treino
    exercise_histories = ExerciseHistory.objects.filter(
        workout_history__workout=session.workout
    )

    context = {
        "user": user,
        "session": session,
        "exercise_histories": exercise_histories,
    }
    return render(request, "workout/session_history_detail.html", context)


def current_session(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    # Busca a última sessão de treino que não foi concluída
    last_session = (
        WorkoutSession.objects.filter(user=user, workout__completed=False)
        .order_by("-date")
        .first()
    )

    if last_session:
        return redirect("view_session", id=last_session.id)

    # Busca o próximo treino que ainda não foi concluído, com base no order_id
    next_workout = (
        Workout.objects.filter(user=user, completed=False).order_by("order_id").first()
    )

    if next_workout:
        # Criar uma nova sessão para o próximo treino
        new_session = WorkoutSession.objects.create(
            user=user, workout=next_workout, date=timezone.now()
        )
        return redirect("view_session", id=new_session.id)
    else:
        # Se todos os treinos foram concluídos, redefinir para começar novamente
        Workout.objects.filter(user=user).update(completed=False)
        messages.info(
            request,
            "Todos os treinos foram concluídos. Reiniciando a sequência de treinos.",
        )

        # Busca o próximo treino após resetar os treinos
        first_workout = Workout.objects.filter(user=user).order_by("order_id").first()
        if first_workout:
            new_session = WorkoutSession.objects.create(
                user=user, workout=first_workout, date=timezone.now()
            )
            return redirect("view_session", id=new_session.id)

        return redirect(
            "all_workouts"
        )  # Caso não haja treinos, redireciona para a lista de treinos


def importar_treinos(request):
    user = get_logged_in_user(request)
    if not user:
        return redirect("/")

    if request.method == "POST":
        arquivo_excel = request.FILES["arquivo_excel"]
        df = pd.read_excel(arquivo_excel)

        # Remover espaços em branco dos nomes das colunas
        df.columns = df.columns.str.strip()

        # Verificar se a coluna order_id está presente
        if "order_id" not in df.columns:
            messages.error(
                request,
                "Erro ao importar treinos: coluna 'order_id' não encontrada.",
            )
            return redirect("all_workouts")

        # Iterar sobre cada ordem de treino única
        for ordem in df["order_id"].unique():
            exercicios = df[df["order_id"] == ordem]

            # Criar um novo treino, agora com o nome do grupo no campo de nome
            treino = Workout.objects.create(
                name=f'{exercicios["Grupo"].iloc[0]}',  # Nome será o Grupo
                description=f"Treino {ordem}",  # Descrição será Treino 1, 2, 3...
                user=user,
                order_id=ordem,  # Usar o order_id do Excel
            )

            # Iterar sobre cada exercício desse treino
            for _, linha in exercicios.iterrows():
                Exercise.objects.create(
                    name=linha["Exercicio"],
                    sets=linha["séries"],
                    repetitions=linha["repetições"],
                    rpe=linha["RPE"],
                    workout=treino,
                )

        messages.success(request, "Treinos importados com sucesso!")
        return redirect("all_workouts")

    return render(request, "workout/all_workouts.html")


# Página de Termos de Uso
def tos(request):
    return render(request, "workout/legal/tos.html")
