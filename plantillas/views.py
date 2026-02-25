from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def plantilla_lista(request):
    return render(request, 'plantillas/lista.html', {})