from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Workout, Exercise, WorkoutSession, ExerciseSession

User = get_user_model()


class WorkoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password"
        )
        self.client.login(username="testuser", password="password")
        self.workout = Workout.objects.create(
            name="Treino A", description="Treino de pernas", user=self.user
        )

    def test_new_workout_get(self):
        response = self.client.get(reverse("new_workout"))
        self.assertEqual(
            response.status_code, 200
        )  # Espera-se que a página de criação seja carregada

    def test_new_workout_post_success(self):
        workout_data = {
            "name": "Treino B",
            "description": "Treino de braços",
        }
        response = self.client.post(reverse("new_workout"), workout_data)
        self.assertEqual(response.status_code, 302)  # Redireciona após sucesso
        self.assertTrue(
            Workout.objects.filter(name="Treino B").exists()
        )  # Verifica se o treino foi criado

    def test_edit_workout_get(self):
        response = self.client.get(reverse("edit_workout", args=[self.workout.id]))
        self.assertEqual(
            response.status_code, 200
        )  # Verifica se a página de edição foi carregada

    def test_edit_workout_post(self):
        update_data = {
            "name": "Treino A Atualizado",
            "description": "Treino de pernas atualizado",
        }
        response = self.client.post(
            reverse("edit_workout", args=[self.workout.id]), update_data
        )
        self.assertEqual(response.status_code, 302)  # Redireciona após sucesso
        self.workout.refresh_from_db()  # Atualiza o objeto da base de dados
        self.assertEqual(self.workout.name, "Treino A Atualizado")

    def test_delete_workout(self):
        response = self.client.post(reverse("delete_workout", args=[self.workout.id]))
        self.assertEqual(response.status_code, 302)  # Redireciona após exclusão
        self.assertFalse(
            Workout.objects.filter(id=self.workout.id).exists()
        )  # Verifica se o treino foi excluído


class WorkoutSessionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password"
        )
        self.client.login(username="testuser", password="password")
        self.workout = Workout.objects.create(
            name="Treino A", description="Treino de pernas", user=self.user
        )

    def test_start_workout_session(self):
        response = self.client.post(
            reverse("start_workout_session", args=[self.workout.id])
        )
        self.assertEqual(
            response.status_code, 302
        )  # Verifica redirecionamento para sessão
        self.assertTrue(
            WorkoutSession.objects.filter(workout=self.workout).exists()
        )  # Verifica se a sessão foi criada

    def test_complete_workout(self):
        exercise = Exercise.objects.create(
            name="Agachamento", sets=4, repetitions=12, rpe=8, workout=self.workout
        )
        response = self.client.post(
            reverse("complete_workout", args=[self.workout.id]),
            {f"weight_{exercise.id}": 50, f"reps_{exercise.id}": 10},
        )
        self.assertEqual(response.status_code, 302)  # Redireciona após completar
        self.assertTrue(
            WorkoutSession.objects.filter(workout=self.workout, user=self.user).exists()
        )
        exercise_session = ExerciseSession.objects.get(exercise=exercise)
        self.assertEqual(exercise_session.weight_used, 50)
        self.assertEqual(exercise_session.actual_repetitions, 10)

    def test_view_session(self):
        workout_session = WorkoutSession.objects.create(
            workout=self.workout, user=self.user
        )
        response = self.client.get(reverse("view_session", args=[workout_session.id]))
        self.assertEqual(
            response.status_code, 200
        )  # A página de sessão deve ser exibida


class AllWorkoutsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password"
        )
        self.client.login(username="testuser", password="password")
        self.workout = Workout.objects.create(
            name="Treino A", description="Treino de pernas", user=self.user
        )

    def test_all_workouts_view(self):
        response = self.client.get(reverse("all_workouts"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "workout/all_workouts.html")
        self.assertContains(response, self.workout.name)
