from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Workout, Exercise, WorkoutSession, ExerciseSession

User = get_user_model()


class WorkoutManagerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password"
        )

    def test_create_workout_success(self):
        # Testando a criação bem-sucedida de um workout
        workout_data = {
            "name": "Treino A",
            "description": "Treino para braços",
            "user": self.user,
            "repeat_days": 30,
        }
        result = Workout.objects.create_workout(**workout_data)
        self.assertIn("workout", result)
        workout = result["workout"]
        self.assertEqual(workout.name, "Treino A")
        self.assertEqual(workout.description, "Treino para braços")
        self.assertEqual(workout.user, self.user)

    def test_create_workout_failure(self):
        # Testando a falha de criação por nome curto
        workout_data = {
            "name": "A",  # Nome com menos de 2 caracteres
            "description": "Treino para braços",
            "user": self.user,
            "repeat_days": 30,
        }
        result = Workout.objects.create_workout(**workout_data)
        self.assertIn("errors", result)
        self.assertEqual(
            result["errors"][0],
            "O nome é obrigatório e deve ter pelo menos 2 caracteres.",
        )

        # Testando a falha de criação por descrição curta
        workout_data["name"] = "Treino A"
        workout_data["description"] = "A"  # Descrição com menos de 2 caracteres
        result = Workout.objects.create_workout(**workout_data)
        self.assertIn("errors", result)
        self.assertEqual(
            result["errors"][0],
            "A descrição é obrigatória e deve ter pelo menos 2 caracteres.",
        )


class ExerciseManagerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password"
        )
        self.workout = Workout.objects.create(
            name="Treino A",
            description="Treino de pernas",
            user=self.user,
            repeat_days=30,
        )

    def test_create_exercise_success(self):
        # Testando a criação bem-sucedida de um exercício
        exercise_data = {
            "name": "Agachamento",
            "sets": 4,
            "repetitions": 12,
            "rpe": 8,
            "workout": self.workout,
        }
        result = Exercise.objects.create_exercise(**exercise_data)
        self.assertIn("exercise", result)
        exercise = result["exercise"]
        self.assertEqual(exercise.name, "Agachamento")
        self.assertEqual(exercise.sets, 4)
        self.assertEqual(exercise.repetitions, 12)
        self.assertEqual(exercise.rpe, 8)

    def test_create_exercise_failure(self):
        # Testando a falha de criação por nome curto
        exercise_data = {
            "name": "A",  # Nome com menos de 2 caracteres
            "sets": 4,
            "repetitions": 12,
            "rpe": 8,
            "workout": self.workout,
        }
        result = Exercise.objects.create_exercise(**exercise_data)
        self.assertIn("errors", result)
        self.assertEqual(
            result["errors"][0],
            "O nome do exercício é obrigatório e deve ter pelo menos 2 caracteres.",
        )

        # Testando a falha de criação por valores inválidos
        exercise_data["name"] = "Agachamento"
        exercise_data["sets"] = -1  # Valor inválido para sets
        result = Exercise.objects.create_exercise(**exercise_data)
        self.assertIn("errors", result)
        self.assertEqual(
            result["errors"][0],
            "Séries, repetições devem ser positivos e RPE entre 1 e 10.",
        )


class WorkoutSessionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password"
        )
        self.workout = Workout.objects.create(
            name="Treino A",
            description="Treino de pernas",
            user=self.user,
            repeat_days=30,
        )

    def test_create_workout_session(self):
        # Testando a criação de uma sessão de treino
        workout_session = WorkoutSession.objects.create(
            user=self.user, workout=self.workout
        )
        self.assertEqual(workout_session.user, self.user)
        self.assertEqual(workout_session.workout, self.workout)
        self.assertFalse(workout_session.completed)

    def test_create_exercise_sessions(self):
        # Criar exercícios para o treino
        Exercise.objects.create(
            name="Agachamento", sets=4, repetitions=12, rpe=8, workout=self.workout
        )
        Exercise.objects.create(
            name="Leg Press", sets=3, repetitions=10, rpe=7, workout=self.workout
        )

        # Criar a sessão de treino
        workout_session = WorkoutSession.objects.create(
            user=self.user, workout=self.workout
        )
        workout_session.create_exercise_sessions()

        # Verificar se os exercícios da sessão foram criados
        exercises_sessions = ExerciseSession.objects.filter(
            workout_session=workout_session
        )
        self.assertEqual(exercises_sessions.count(), 2)
        self.assertEqual(exercises_sessions[0].exercise.name, "Agachamento")
        self.assertEqual(exercises_sessions[1].exercise.name, "Leg Press")
