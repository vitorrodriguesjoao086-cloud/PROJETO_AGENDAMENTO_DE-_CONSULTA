"""
Script para criar dados de exemplo.
Rode com: python seed_data.py
"""
import json, hashlib
from datetime import date, timedelta
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent / "dados"


def hash_senha(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()


def main():
    PASTA_DADOS.mkdir(exist_ok=True)
    (PASTA_DADOS / 'sessions').mkdir(exist_ok=True)

    usuarios = [
        {'id': 'u1', 'full_name': 'Admin Sistema', 'email': 'admin@medagenda.com',
         'password_hash': hash_senha('admin123'), 'role': 'admin'},
        {'id': 'u2', 'full_name': 'Maria Recepcao', 'email': 'recepcao@medagenda.com',
         'password_hash': hash_senha('recepcao123'), 'role': 'receptionist'},
    ]

    medicos = [
        {'id': 'd1', 'full_name': 'Dr. Daniel Mota', 'specialty': 'Cardiologia', 'crm': 'CRM/PE 12345', 'available': True},
        {'id': 'd2', 'full_name': 'Dra. Beatriz Lima', 'specialty': 'Neurologia', 'crm': 'CRM/PE 23456', 'available': True},
        {'id': 'd3', 'full_name': 'Dr. Paulo Ramos', 'specialty': 'Ortopedia', 'crm': 'CRM/PE 34567', 'available': True},
        {'id': 'd4', 'full_name': 'Dra. Carla Souza', 'specialty': 'Clinica Geral', 'crm': 'CRM/PE 45678', 'available': True},
    ]

    salas = [{'id': f'r{i}', 'name': f'Sala 0{i}', 'active': True} for i in range(1, 5)]

    nomes = ['Ana Silva', 'Roberto Ferreira', 'Mariana Souza', 'Carlos Lima',
             'Fernanda Oliveira', 'Joao Alves', 'Luciana Martins', 'Thiago Barbosa']

    pacientes = [
        {'id': f'p{i}', 'full_name': n, 'email': f'{n.split()[0].lower()}{i}@email.com',
         'phone': f'(81) 9{i:04d}-{i*1111%9999:04d}',
         'birth_date': f'19{80+i%20}-{i%12+1:02d}-{i%28+1:02d}',
         'notes': '', 'created_at': '2026-01-01T00:00:00'}
        for i, n in enumerate(nomes, 1)
    ]

    hoje = date.today()
    horarios = ['08:00', '09:00', '10:00', '11:00', '14:00', '15:00']
    tipos = ['first_visit', 'return', 'urgent']
    status_lista = ['confirmed', 'pending', 'cancelled']

    consultas = []
    for i in range(12):
        h = horarios[i % len(horarios)]
        consultas.append({
            'id': f'a{i+1}',
            'patient_id': f'p{i % len(pacientes) + 1}',
            'doctor_id': f'd{i % len(medicos) + 1}',
            'room_id': f'r{i % len(salas) + 1}',
            'date': (hoje + timedelta(days=i % 8 - 3)).isoformat(),
            'start_time': h,
            'end_time': f'{int(h.split(":")[0]):02d}:30',
            'type': tipos[i % len(tipos)],
            'status': status_lista[i % len(status_lista)],
            'notes': '', 'created_by': 'u1',
            'created_at': '2026-05-01T10:00:00',
        })

    arquivos = {
        'users.json': usuarios, 'doctors.json': medicos,
        'rooms.json': salas, 'patients.json': pacientes,
        'appointments.json': consultas,
    }
    for nome, dados in arquivos.items():
        with open(PASTA_DADOS / nome, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print(f'[OK] {nome} ({len(dados)} registros)')

    print('\n[OK] Dados criados com sucesso!')
    print('Login: admin@medagenda.com / admin123')


if __name__ == '__main__':
    main()
