# apps/workout/context_processors.py
from .models import WorkoutSession, WorkoutPlan
from django.utils import timezone


def current_session_status(request):
    user = request.user
    context = {
        "has_session": False,
        "current_session_id": None,
        "has_plan": False,
    }

    if user.is_authenticated:
        # Busca a sessão atual em andamento
        current_session = (
            WorkoutSession.objects.filter(user=user, date__lte=timezone.now())
            .order_by("-date")
            .first()
        )

        if current_session:
            context["has_session"] = True
            context["current_session_id"] = current_session.id

        # Verifica se o usuário tem um plano de treino
        plan = WorkoutPlan.objects.filter(user=user).first()
        context["has_plan"] = bool(plan)

    return context
