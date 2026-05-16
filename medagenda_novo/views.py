import hashlib
from datetime import date
from functools import wraps
from django.shortcuts import render, redirect
from django.contrib import messages
import data_store as ds


def login_obrigatorio(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def _carregar_refs():
    return (
        {d['id']: d for d in ds.carregar('doctors.json')},
        {p['id']: p for p in ds.carregar('patients.json')},
        {r['id']: r for r in ds.carregar('rooms.json')},
    )


def _enriquecer(consulta, medicos, pacientes, salas):
    c = dict(consulta)
    c['doctor'] = medicos.get(c.get('doctor_id'), {})
    c['patient'] = pacientes.get(c.get('patient_id'), {})
    c['room'] = salas.get(c.get('room_id'), {})
    return c


def _calcular_fim(inicio):
    try:
        h, m = map(int, inicio.split(':'))
        t = h * 60 + m + 30
        return f"{t // 60:02d}:{t % 60:02d}"
    except Exception:
        return inicio


def _tem_conflito(consultas, doctor_id, data, inicio, fim, excluir_id=None):
    for c in consultas:
        if c.get('id') == excluir_id or c.get('status') == 'cancelled':
            continue
        if c.get('doctor_id') == doctor_id and c.get('date') == data:
            if inicio < c.get('end_time', '') and fim > c.get('start_time', ''):
                return True
    return False


# --- LOGIN / LOGOUT ---

def login(request):
    if request.session.get('user_id'):
        return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('password', '')
        usuario = next((u for u in ds.carregar('users.json') if u['email'] == email), None)
        if usuario:
            senha_hash = hashlib.sha256(senha.encode('utf-8')).hexdigest()
            if senha_hash == usuario['password_hash']:
                request.session['user_id'] = usuario['id']
                request.session['user_name'] = usuario['full_name']
                request.session['user_role'] = usuario['role']
                return redirect('dashboard')
        messages.error(request, 'E-mail ou senha invalidos.')
    return render(request, 'login.html')


def logout(request):
    request.session.flush()
    return redirect('login')


# --- DASHBOARD ---

@login_obrigatorio
def dashboard(request):
    hoje = date.today().isoformat()
    medicos, pacientes, salas = _carregar_refs()
    todas = ds.carregar('appointments.json')

    consultas_hoje = []
    for c in todas:
        if c['date'] == hoje:
            consultas_hoje.append(_enriquecer(c, medicos, pacientes, salas))
    consultas_hoje.sort(key=lambda x: x.get('start_time', ''))

    return render(request, 'dashboard.html', {
        'appointments': consultas_hoje,
        'selected_date': date.today(),
        'metrics': {
            'total': len(consultas_hoje),
            'confirmed': sum(1 for c in consultas_hoje if c['status'] == 'confirmed'),
            'pending': sum(1 for c in consultas_hoje if c['status'] == 'pending'),
            'cancelled': sum(1 for c in consultas_hoje if c['status'] == 'cancelled'),
        }
    })


# --- CONSULTAS ---

@login_obrigatorio
def consultas_lista(request):
    medicos, pacientes, salas = _carregar_refs()
    busca = request.GET.get('search', '').lower()
    status = request.GET.get('status', '')

    resultado = [_enriquecer(c, medicos, pacientes, salas) for c in ds.carregar('appointments.json')]

    if busca:
        resultado = [c for c in resultado if
                     busca in c['patient'].get('full_name', '').lower() or
                     busca in c['doctor'].get('full_name', '').lower()]
    if status:
        resultado = [c for c in resultado if c.get('status') == status]

    resultado.sort(key=lambda x: (x.get('date', ''), x.get('start_time', '')), reverse=True)

    return render(request, 'consultas_lista.html', {
        'appointments': resultado, 'search_q': busca,
        'status_f': status, 'statuses': ['pending', 'confirmed', 'cancelled', 'urgent'],
    })


@login_obrigatorio
def consulta_nova(request):
    medicos = ds.carregar('doctors.json')
    pacientes = ds.carregar('patients.json')
    salas = ds.carregar('rooms.json')

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        data = request.POST.get('date')
        inicio = request.POST.get('start_time')
        fim = _calcular_fim(inicio)

        if _tem_conflito(ds.carregar('appointments.json'), doctor_id, data, inicio, fim):
            messages.error(request, 'Conflito de horario! O medico ja tem consulta nesse horario.')
        else:
            tipo = request.POST.get('type', 'first_visit')
            ds.criar('appointments.json', {
                'patient_id': request.POST.get('patient_id'),
                'doctor_id': doctor_id,
                'room_id': request.POST.get('room_id'),
                'date': data, 'start_time': inicio, 'end_time': fim,
                'type': tipo,
                'status': 'urgent' if tipo == 'urgent' else 'pending',
                'notes': request.POST.get('notes', ''),
                'created_by': request.session.get('user_id'),
            })
            messages.success(request, 'Consulta agendada com sucesso!')
            return redirect('consultas_lista')

    return render(request, 'consulta_form.html', {
        'doctors': medicos, 'patients': pacientes, 'rooms': salas,
        'form_data': request.POST.dict() if request.method == 'POST' else {},
        'today': date.today().isoformat(),
    })


@login_obrigatorio
def consulta_detalhe(request, consulta_id):
    consulta = ds.buscar_por_id('appointments.json', consulta_id)
    if not consulta:
        messages.error(request, 'Consulta nao encontrada.')
        return redirect('consultas_lista')
    medicos, pacientes, salas = _carregar_refs()
    return render(request, 'consulta_detalhe.html', {
        'appt': _enriquecer(consulta, medicos, pacientes, salas)
    })


@login_obrigatorio
def consulta_editar(request, consulta_id):
    consulta = ds.buscar_por_id('appointments.json', consulta_id)
    if not consulta:
        return redirect('consultas_lista')

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        data = request.POST.get('date')
        inicio = request.POST.get('start_time')
        fim = _calcular_fim(inicio)

        if _tem_conflito(ds.carregar('appointments.json'), doctor_id, data, inicio, fim, excluir_id=consulta_id):
            messages.error(request, 'Conflito de horario! Escolha outro horario.')
        else:
            ds.atualizar('appointments.json', consulta_id, {
                'patient_id': request.POST.get('patient_id'),
                'doctor_id': doctor_id,
                'room_id': request.POST.get('room_id'),
                'date': data, 'start_time': inicio, 'end_time': fim,
                'type': request.POST.get('type', 'first_visit'),
                'notes': request.POST.get('notes', ''),
            })
            messages.success(request, 'Consulta atualizada!')
            return redirect('consulta_detalhe', consulta_id=consulta_id)

    return render(request, 'consulta_form.html', {
        'doctors': ds.carregar('doctors.json'),
        'patients': ds.carregar('patients.json'),
        'rooms': ds.carregar('rooms.json'),
        'form_data': consulta, 'appt': consulta,
        'today': date.today().isoformat(), 'editing': True,
    })


@login_obrigatorio
def consulta_confirmar(request, consulta_id):
    if request.method == 'POST':
        ds.atualizar('appointments.json', consulta_id, {'status': 'confirmed'})
        messages.success(request, 'Consulta confirmada!')
    return redirect('consulta_detalhe', consulta_id=consulta_id)


@login_obrigatorio
def consulta_cancelar(request, consulta_id):
    consulta = ds.buscar_por_id('appointments.json', consulta_id)
    if not consulta:
        return redirect('consultas_lista')
    if request.method == 'POST':
        ds.atualizar('appointments.json', consulta_id, {'status': 'cancelled'})
        messages.success(request, 'Consulta cancelada.')
        return redirect('consultas_lista')
    medicos, pacientes, salas = _carregar_refs()
    return render(request, 'consulta_cancelar.html', {
        'appt': _enriquecer(consulta, medicos, pacientes, salas)
    })


# --- PACIENTES ---

@login_obrigatorio
def pacientes_lista(request):
    pacientes = ds.carregar('patients.json')
    busca = request.GET.get('search', '').lower()
    if busca:
        pacientes = [p for p in pacientes if busca in p.get('full_name', '').lower()]
    return render(request, 'pacientes_lista.html', {'patients': pacientes, 'search_q': busca})


@login_obrigatorio
def paciente_novo(request):
    if request.method == 'POST':
        ds.criar('patients.json', {
            'full_name': request.POST.get('full_name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'birth_date': request.POST.get('birth_date'),
            'notes': request.POST.get('notes', ''),
        })
        messages.success(request, 'Paciente cadastrado!')
        return redirect('pacientes_lista')
    return render(request, 'paciente_form.html', {'form_data': {}})


@login_obrigatorio
def paciente_detalhe(request, paciente_id):
    paciente = ds.buscar_por_id('patients.json', paciente_id)
    if not paciente:
        return redirect('pacientes_lista')
    consultas = [a for a in ds.carregar('appointments.json') if a.get('patient_id') == paciente_id]
    medicos = {d['id']: d for d in ds.carregar('doctors.json')}
    for c in consultas:
        c['doctor'] = medicos.get(c.get('doctor_id'), {})
    consultas.sort(key=lambda x: x.get('date', ''), reverse=True)
    return render(request, 'paciente_detalhe.html', {'patient': paciente, 'appointments': consultas})


@login_obrigatorio
def paciente_editar(request, paciente_id):
    paciente = ds.buscar_por_id('patients.json', paciente_id)
    if not paciente:
        return redirect('pacientes_lista')
    if request.method == 'POST':
        ds.atualizar('patients.json', paciente_id, {
            'full_name': request.POST.get('full_name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'birth_date': request.POST.get('birth_date'),
            'notes': request.POST.get('notes', ''),
        })
        messages.success(request, 'Paciente atualizado!')
        return redirect('paciente_detalhe', paciente_id=paciente_id)
    return render(request, 'paciente_form.html', {'form_data': paciente, 'editing': True})


# --- MEDICOS ---

@login_obrigatorio
def medicos_lista(request):
    return render(request, 'medicos_lista.html', {'doctors': ds.carregar('doctors.json')})
