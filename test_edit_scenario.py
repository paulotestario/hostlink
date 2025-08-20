import sqlite3
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório atual ao path para importar database
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database

# Obter instância do banco de dados
db = get_database()

print("=== Teste de Cenário de Edição de Avaliações ===")
print()

booking_id = 6
user_id = 1
listing_id = 1

# 1. Verificar se a reserva existe
print("1. Verificando reserva...")
try:
    # Buscar reserva diretamente no Supabase
    booking_result = db.supabase.table('listing_bookings').select(
        '*, user_listings(title)'
    ).eq('id', booking_id).execute()
    
    if booking_result.data:
        booking = booking_result.data[0]
        print(f"   ✓ Reserva {booking_id} encontrada")
        print(f"   Status: {booking.get('status', 'N/A')}")
        print(f"   Usuário: {booking.get('guest_user_id', 'N/A')}")
        print(f"   Listing: {booking.get('listing_id', 'N/A')}")
        if booking.get('user_listings'):
            print(f"   Título: {booking['user_listings'].get('title', 'N/A')}")
    else:
        print(f"   ✗ Reserva {booking_id} não encontrada")
        exit(1)
except Exception as e:
    print(f"   Erro ao buscar reserva: {e}")
    exit(1)

print()

# 2. Verificar se já existe avaliação
print("2. Verificando avaliação existente...")
try:
    existing_review = db.get_booking_review(booking_id)
    if existing_review:
        print(f"   ✓ Avaliação encontrada (ID: {existing_review.get('id')})")
        print(f"   Criada em: {existing_review.get('created_at')}")
        print(f"   Título: {existing_review.get('title')}")
        
        # Verificar se pode editar
        edit_check = db.can_user_edit_review(user_id, booking_id)
        print(f"   Pode editar: {edit_check.get('can_edit', False)}")
        if edit_check.get('reason'):
            print(f"   Motivo: {edit_check.get('reason')}")
    else:
        print("   Nenhuma avaliação encontrada")
        
        # Criar uma avaliação de teste
        print("   Criando avaliação de teste...")
        
        try:
            review_id = db.create_review(
                booking_id=booking_id,
                overall_rating=5,
                cleanliness_rating=4,
                communication_rating=5,
                checkin_rating=4,
                accuracy_rating=5,
                location_rating=4,
                value_rating=5,
                review_title='Hospedagem excelente!',
                review_comment='Tudo perfeito, recomendo muito!',
                would_recommend=True
            )
            print(f"   ✓ Avaliação criada com ID: {review_id}")
            
            # Verificar novamente se pode editar
            edit_check = db.can_user_edit_review(user_id, booking_id)
            print(f"   Pode editar: {edit_check.get('can_edit', False)}")
            
        except Exception as e:
            print(f"   Erro ao criar avaliação: {e}")
except Exception as e:
    print(f"   Erro ao verificar avaliação: {e}")

print()

# 3. Testar edição (se possível)
print("3. Testando edição...")
try:
    edit_check = db.can_user_edit_review(user_id, booking_id)
    
    if edit_check.get('can_edit'):
        print("   ✓ Edição permitida")
        
        # Dados atualizados
        updated_data = {
            'overall_rating': 4,
            'cleanliness_rating': 5,
            'communication_rating': 4,
            'checkin_rating': 5,
            'accuracy_rating': 4,
            'location_rating': 5,
            'value_rating': 4,
            'title': 'Hospedagem ATUALIZADA!',
            'comment': 'Comentário editado após criação inicial.',
            'would_recommend': True,
            'is_public': True
        }
        
        try:
            success = db.update_review(
                booking_id=booking_id,
                user_id=user_id,
                overall_rating=updated_data['overall_rating'],
                cleanliness_rating=updated_data['cleanliness_rating'],
                communication_rating=updated_data['communication_rating'],
                checkin_rating=updated_data['checkin_rating'],
                accuracy_rating=updated_data['accuracy_rating'],
                location_rating=updated_data['location_rating'],
                value_rating=updated_data['value_rating'],
                title=updated_data['title'],
                comment=updated_data['comment'],
                would_recommend=updated_data['would_recommend'],
                is_public=updated_data['is_public']
            )
            
            if success:
                print("   ✓ Avaliação atualizada com sucesso!")
                
                # Verificar a avaliação atualizada
                updated_review = db.get_booking_review(booking_id)
                if updated_review:
                    print(f"   Novo título: {updated_review.get('review_title')}")
                    print(f"   Nova nota geral: {updated_review.get('overall_rating')}")
            else:
                print("   ✗ Falha ao atualizar avaliação")
        except Exception as e:
            print(f"   Erro ao atualizar avaliação: {e}")
    else:
        reason = edit_check.get('reason', 'Motivo não especificado')
        print(f"   ✗ Edição não permitida: {reason}")
        
except Exception as e:
    print(f"   Erro ao testar edição: {e}")

print()
print("=== Teste Concluído ===")
print(f"Acesse: http://localhost:5000/avaliar-hospedagem?booking_id={booking_id}")
print("Para testar a interface web.")