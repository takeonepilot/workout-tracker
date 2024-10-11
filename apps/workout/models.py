from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
import re


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
    def new(self, **kwargs):
        errors = []

        if len(kwargs["name"]) < 2:
            errors.append("Name is required and must be at least 2 characters long.")

        WORKOUT_REGEX = re.compile(r"^[\w\s!@#$%^&*()?]*$")
        if not WORKOUT_REGEX.match(kwargs["name"]):
            errors.append("Name must contain valid characters.")

        if len(kwargs["description"]) < 2:
            errors.append(
                "Description is required and must be at least 2 characters long."
            )
        if not WORKOUT_REGEX.match(kwargs["description"]):
            errors.append("Description must contain valid characters.")

        if not errors:
            workout = Workout(
                name=kwargs["name"],
                description=kwargs["description"],
                user=kwargs["user"],
            )
            workout.save()
            return {"workout": workout}
        else:
            return {"errors": errors}


class Workout(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=150)
    completed = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    repeat_days = models.IntegerField(default=30)

    objects = WorkoutManager()


class ExerciseManager(models.Manager):
    def new(self, **kwargs):
        errors = []

        if len(kwargs["name"]) < 2:
            errors.append(
                "O nome do exercício é obrigatório e deve ter pelo menos 2 caracteres."
            )

        try:
            kwargs["sets"] = int(kwargs["sets"])
            kwargs["repetitions"] = int(kwargs["repetitions"])
            kwargs["rpe"] = int(kwargs["rpe"])

            if (
                kwargs["sets"] <= 0
                or kwargs["repetitions"] <= 0
                or not (1 <= kwargs["rpe"] <= 10)
            ):
                errors.append(
                    "Séries, repetições e RPE devem ser números positivos, e o RPE deve estar entre 1 e 10."
                )
        except ValueError:
            errors.append("Séries, repetições e RPE devem ser números válidos.")

        if not errors:
            exercise = Exercise(
                name=kwargs["name"],
                sets=kwargs["sets"],
                repetitions=kwargs["repetitions"],
                rpe=kwargs["rpe"],
                workout=kwargs["workout"],
            )
            exercise.save()
            return {"exercise": exercise}
        else:
            return {"errors": errors}


class Exercise(models.Model):
    name = models.CharField(max_length=50)
    sets = models.IntegerField(default=1)
    repetitions = models.IntegerField()
    rpe = models.IntegerField(default=8)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ExerciseManager()

    def __str__(self):
        return f"{self.name} - {self.sets}x{self.repetitions} RPE {self.rpe}"


class WorkoutSession(models.Model):
    workout_plan = models.ForeignKey(Workout, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sessão de {self.workout_plan.name} em {self.date}"


class ExerciseSession(models.Model):
    exercise_plan = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    workout_session = models.ForeignKey(
        WorkoutSession, related_name="exercise_sessions", on_delete=models.CASCADE
    )
    weight_used = models.DecimalField(max_digits=5, decimal_places=1)
    actual_repetitions = models.IntegerField()
    sets = models.IntegerField(default=1)
    rpe = models.IntegerField()

    def __str__(self):
        return f"{self.exercise_plan.name} - {self.weight_used}kg x {self.actual_repetitions} reps, {self.sets} séries"


class ExerciseLog(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    performed_weight = models.DecimalField(
        max_digits=5, decimal_places=1
    )  # Peso utilizado na série
    performed_repetitions = models.IntegerField()  # Repetições realizadas
    date = models.DateTimeField(auto_now_add=True)
    exercise_session = models.ForeignKey(ExerciseSession, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.exercise.name} - {self.performed_weight}kg x {self.performed_repetitions} reps em {self.date}"
