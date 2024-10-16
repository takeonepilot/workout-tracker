# models.py
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
import re
import json


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O campo de e-mail deve ser preenchido.")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(
            password
        )  # Utiliza a função nativa do Django para hash da senha
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser deve ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser deve ter is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)

    def register(self, **kwargs):
        errors = []

        # Validate username
        if len(kwargs["username"][0]) < 2:
            errors.append(
                "Username is required and must be at least 2 characters long."
            )

        USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9!@#$%^&*()?]*$")
        if not USERNAME_REGEX.match(kwargs["username"][0]):
            errors.append(
                "Username must contain letters, numbers, and basic characters only."
            )

        if User.objects.filter(username=kwargs["username"][0]).exists():
            errors.append("Username is already registered to another user.")

        # Validate email
        if len(kwargs["email"][0]) < 5:
            errors.append("Email field must be at least 5 characters.")
        EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$")
        if not EMAIL_REGEX.match(kwargs["email"][0]):
            errors.append("Email is not a valid email format.")
        elif User.objects.filter(email=kwargs["email"][0]).exists():
            errors.append("Email address is already registered to another user.")

        # Validate password
        if (
            len(kwargs["password"][0]) < 8
            or kwargs["password"][0] != kwargs["password_confirmation"][0]
        ):
            errors.append(
                "Password fields are required and must match and be at least 8 characters."
            )

        # Validate TOS acceptance
        if kwargs["tos_accept"][0] != "on":
            errors.append("Terms of service must be accepted.")

        # If no errors, create user
        if not errors:
            user = User(
                username=kwargs["username"][0],
                email=kwargs["email"][0],
            )
            user.set_password(
                kwargs["password"][0]
            )  # Hash da senha usando a função nativa
            user.tos_accept = True
            user.save()
            return {"logged_in_user": user}
        else:
            return {"errors": errors}

    def login(self, **kwargs):
        errors = []
        username = kwargs.get("username", [""])[0]
        password = kwargs.get("password", [""])[0]

        if not username or not password:
            errors.append("Nome de usuário e senha são obrigatórios.")
            return {"errors": errors}

        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return {"logged_in_user": user}
            else:
                errors.append("Nome de usuário ou senha estão incorretos.")
        except User.DoesNotExist:
            errors.append("Nome de usuário ou senha estão incorretos.")

        return {"errors": errors}


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=50, unique=True)
    password = models.CharField(max_length=60)
    tos_accept = models.BooleanField(default=False)
    level = models.IntegerField(default=1)
    level_name = models.CharField(max_length=15, default="Iniciante")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username


class WorkoutManager(models.Manager):
    def create_workout(self, **kwargs):
        errors = []
        # Validação básica do nome e descrição
        if len(kwargs.get("name", "")) < 2:
            errors.append("O nome é obrigatório e deve ter pelo menos 2 caracteres.")
        if len(kwargs.get("description", "")) < 2:
            errors.append(
                "A descrição é obrigatória e deve ter pelo menos 2 caracteres."
            )
        if kwargs.get("order_id", 0) <= 0:
            errors.append("A ordem do treino é obrigatória e deve ser maior que 0.")

        if errors:
            return {"errors": errors}

        # Criar e salvar o Workout
        workout = self.create(
            name=kwargs["name"],
            description=kwargs["description"],
            user=kwargs["user"],
            order_id=kwargs["order_id"],
        )
        return {"workout": workout}


class Workout(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=150)
    completed = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_id = models.PositiveIntegerField(default=0)  # Campo para armazenar a ordem

    objects = WorkoutManager()

    def __str__(self):
        return f"{self.name} - {self.user.username}"


class ExerciseManager(models.Manager):
    def create_exercise(self, **kwargs):
        errors = []
        # Validação do nome do exercício
        if len(kwargs.get("name", "")) < 2:
            errors.append(
                "O nome do exercício é obrigatório e deve ter pelo menos 2 caracteres."
            )
        try:
            sets = int(kwargs.get("sets", 1))
            repetitions = int(kwargs.get("repetitions", 1))
            rpe = int(kwargs.get("rpe", 8))
            if sets <= 0 or repetitions <= 0 or not (1 <= rpe <= 10):
                errors.append(
                    "Séries, repetições devem ser positivos e RPE entre 1 e 10."
                )
        except ValueError:
            errors.append("Séries, repetições e RPE devem ser números válidos.")

        if errors:
            return {"errors": errors}

        # Criar e salvar o Exercise
        exercise = self.create(
            name=kwargs["name"],
            sets=sets,
            repetitions=repetitions,
            rpe=rpe,
            workout=kwargs["workout"],
        )
        return {"exercise": exercise}


class Exercise(models.Model):
    name = models.CharField(max_length=50)
    sets = models.PositiveIntegerField(default=1)
    repetitions = models.PositiveIntegerField()
    rpe = models.PositiveIntegerField(default=8)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ExerciseManager()

    def __str__(self):
        return f"{self.name} - {self.sets}x{self.repetitions} RPE {self.rpe}"


class WorkoutSession(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Sessão de {self.workout.name} em {self.date}"

    def create_exercise_sessions(self):
        """Método para criar ExerciseSession ao iniciar uma WorkoutSession."""
        exercises = self.workout.exercise_set.all()

        if not exercises:
            print(
                f"Não foram encontrados exercícios para o treino: {self.workout.name}"
            )
            return  # Se não houver exercícios, retorne sem criar

        print(f"Exercícios encontrados para o treino {self.workout.name}: {exercises}")

        for exercise in exercises:
            ExerciseSession.objects.create(
                workout_session=self,
                exercise=exercise,
                weight_used=0,  # Valor padrão
                actual_repetitions=0,
                sets=exercise.sets,
                rpe=exercise.rpe,
            )
            print(f"ExerciseSession criado para o exercício: {exercise.name}")


class ExerciseSession(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    workout_session = models.ForeignKey(
        WorkoutSession, related_name="exercise_sessions", on_delete=models.CASCADE
    )
    weight_used = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    actual_repetitions = models.IntegerField(default=0)
    sets = models.IntegerField(default=1)
    rpe = models.IntegerField()

    def __str__(self):
        return f"{self.exercise.name} ({self.sets} sets, RPE {self.rpe})"


class Series(models.Model):
    exercise_session = models.ForeignKey(
        ExerciseSession, related_name="series", on_delete=models.CASCADE
    )
    weight_used = models.DecimalField(max_digits=5, decimal_places=1)
    repetitions = models.IntegerField()

    def __str__(self):
        return (
            f"Series {self.id} - Weight: {self.weight_used}, Reps: {self.repetitions}"
        )


class WorkoutHistory(models.Model):
    workout = models.ForeignKey(
        Workout, on_delete=models.CASCADE
    )  # Referência ao treino realizado
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Referência ao usuário
    date = models.DateTimeField(auto_now_add=True)  # Data da sessão
    completed = models.BooleanField(default=False)  # Status da sessão

    def __str__(self):
        return f"Sessão de {self.workout.name} em {self.date}"


class ExerciseHistory(models.Model):
    workout_history = models.ForeignKey(
        WorkoutHistory, related_name="exercise_histories", on_delete=models.CASCADE
    )  # Referência ao histórico do treino
    exercise = models.ForeignKey(
        Exercise, on_delete=models.CASCADE
    )  # Referência ao exercício realizado
    weight_used = models.DecimalField(
        max_digits=5, decimal_places=1, default=0.0
    )  # Peso utilizado
    actual_repetitions = models.IntegerField(default=0)  # Repetições reais
    sets = models.IntegerField(default=1)  # Número de séries
    rpe = models.IntegerField()  # RPE (Rate of Perceived Exertion)

    def __str__(self):
        return f"{self.exercise.name} em {self.workout_history.date} - {self.sets}x{self.actual_repetitions} RPE {self.rpe}"
