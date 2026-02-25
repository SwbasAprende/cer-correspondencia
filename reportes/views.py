from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def reporte_lista(request):
    return render(request, 'reportes/lista.html', {})