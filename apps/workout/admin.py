from django.contrib import admin
from .models import User, Workout, Exercise

admin.site.register(User)
admin.site.register(Workout)
admin.site.register(Exercise)
