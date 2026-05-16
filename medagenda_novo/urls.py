from django.urls import path
import views

urlpatterns = [
    # Login
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Consultas
    path('consultas/', views.consultas_lista, name='consultas_lista'),
    path('consultas/nova/', views.consulta_nova, name='consulta_nova'),
    path('consultas/<str:consulta_id>/', views.consulta_detalhe, name='consulta_detalhe'),
    path('consultas/<str:consulta_id>/editar/', views.consulta_editar, name='consulta_editar'),
    path('consultas/<str:consulta_id>/confirmar/', views.consulta_confirmar, name='consulta_confirmar'),
    path('consultas/<str:consulta_id>/cancelar/', views.consulta_cancelar, name='consulta_cancelar'),

    # Pacientes
    path('pacientes/', views.pacientes_lista, name='pacientes_lista'),
    path('pacientes/novo/', views.paciente_novo, name='paciente_novo'),
    path('pacientes/<str:paciente_id>/', views.paciente_detalhe, name='paciente_detalhe'),
    path('pacientes/<str:paciente_id>/editar/', views.paciente_editar, name='paciente_editar'),

    # Medicos
    path('medicos/', views.medicos_lista, name='medicos_lista'),
]
