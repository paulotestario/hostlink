import requests
import json
from datetime import datetime, timedelta

# Configuração
BASE_URL = 'http://localhost:5000'
booking_id = 6

# Dados da avaliação de teste
review_data = {
    'booking_id': booking_id,
    'listing_id': 1,  # Assumindo que existe
    'overall_rating': 5,
    'cleanliness_rating': 4,
    'communication_rating': 5,
    'checkin_rating': 4,
    'accuracy_rating': 5,
    'location_rating': 4,
    'value_rating': 5,
    'title': 'Excelente hospedagem!',
    'comment': 'Tudo perfeito, recomendo muito!',
    'would_recommend': True,
    'is_public': True
}

print("=== Teste de Funcionalidade de Edição de Avaliações ===")
print(f"Testando com booking_id: {booking_id}")
print()

# 1. Verificar se pode avaliar
print("1. Verificando se pode avaliar...")
try:
    response = requests.get(f'{BASE_URL}/api/reviews/can-review/{booking_id}')
    if response.status_code == 200:
        can_review = response.json().get('can_review', False)
        print(f"   Pode avaliar: {can_review}")
    else:
        print(f"   Erro ao verificar: {response.status_code}")
except Exception as e:
    print(f"   Erro na requisição: {e}")

print()

# 2. Criar avaliação
print("2. Criando avaliação...")
try:
    response = requests.post(
        f'{BASE_URL}/api/reviews',
        headers={'Content-Type': 'application/json'},
        json=review_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Avaliação criada com sucesso! ID: {result.get('review_id')}")
    else:
        error_msg = response.json().get('error', 'Erro desconhecido')
        print(f"   Erro ao criar avaliação: {error_msg}")
        if 'já foi avaliada' in error_msg:
            print("   (Avaliação já existe - continuando teste de edição)")
except Exception as e:
    print(f"   Erro na requisição: {e}")

print()

# 3. Verificar se pode editar
print("3. Verificando se pode editar...")
try:
    response = requests.get(f'{BASE_URL}/api/reviews/can-edit/{booking_id}')
    if response.status_code == 200:
        edit_result = response.json()
        can_edit = edit_result.get('can_edit', False)
        reason = edit_result.get('reason', '')
        
        print(f"   Pode editar: {can_edit}")
        if reason:
            print(f"   Motivo: {reason}")
        
        if can_edit and 'review' in edit_result:
            review = edit_result['review']
            print(f"   Avaliação existente encontrada:")
            print(f"     - Título: {review.get('title')}")
            print(f"     - Nota geral: {review.get('overall_rating')}")
            print(f"     - Data: {review.get('created_at')}")
    else:
        print(f"   Erro ao verificar edição: {response.status_code}")
except Exception as e:
    print(f"   Erro na requisição: {e}")

print()

# 4. Testar edição (se possível)
print("4. Testando edição da avaliação...")
updated_review_data = review_data.copy()
updated_review_data.update({
    'title': 'Hospedagem ATUALIZADA!',
    'comment': 'Comentário editado após a criação inicial.',
    'overall_rating': 4  # Mudando a nota
})

try:
    response = requests.put(
        f'{BASE_URL}/api/reviews',
        headers={'Content-Type': 'application/json'},
        json=updated_review_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Avaliação atualizada com sucesso!")
    else:
        error_msg = response.json().get('error', 'Erro desconhecido')
        print(f"   Erro ao atualizar avaliação: {error_msg}")
except Exception as e:
    print(f"   Erro na requisição: {e}")

print()
print("=== Teste Concluído ===")
print(f"Acesse: {BASE_URL}/avaliar-hospedagem?booking_id={booking_id}")
print("Para testar a interface de edição.")