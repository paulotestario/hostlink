#!/usr/bin/env python3
"""
Script de teste para verificar se o salvamento completo de anúncios está funcionando
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database
from datetime import datetime

def test_save_complete_listing():
    """Testa o salvamento de um anúncio com dados completos"""
    
    print("🧪 Testando salvamento completo de anúncio...")
    
    try:
        # Conectar ao banco
        db = get_database()
        if not db:
            print("❌ Erro: Não foi possível conectar ao banco de dados")
            return
        
        # Dados de teste completos
        test_data = {
            'user_id': 1,  # Assumindo que existe um usuário com ID 1
            'title': 'Casa de Praia Completa - Teste',
            'url': 'https://www.airbnb.com.br/rooms/test123456',
            'platform': 'airbnb',
            'property_type': 'Casa inteira',
            'max_guests': 6,
            'bedrooms': 3,
            'bathrooms': 2,
            
            # Dados de preço e avaliação
            'price_per_night': 250.00,
            'rating': 4.8,
            'reviews': 127,
            
            # Localização
            'address': 'Rua das Flores, 123 - Copacabana',
            'latitude': -22.9711,
            'longitude': -43.1822,
            
            # Descrição e mídia
            'description': 'Linda casa de praia com vista para o mar',
            'amenities': ['Wi-Fi', 'Ar-condicionado', 'Piscina', 'Churrasqueira'],
            'image_url': 'https://example.com/image.jpg',
            
            # Características específicas
            'is_beachfront': True,
            'beach_confidence': 0.95,
            'instant_book': True,
            'superhost': True,
            
            # Preços detalhados
            'cleaning_fee': 50.00,
            'service_fee': 35.00,
            'total_price': 335.00,
            
            # Disponibilidade
            'minimum_nights': 2,
            'maximum_nights': 30,
            'availability_365': 300,
            
            # Informações do host
            'host_name': 'João Silva',
            'host_id': 'host123',
            'host_response_rate': 95,
            'host_response_time': 'within an hour',
            
            # Metadados
            'extraction_method': 'test_script',
            'data_quality_score': 1.0
        }
        
        print(f"📝 Dados de teste: {test_data}")
        
        # Salvar anúncio
        listing_id = db.save_user_listing(**test_data)
        
        print(f"✅ Anúncio salvo com sucesso! ID: {listing_id}")
        
        # Verificar se foi salvo corretamente
        saved_listings = db.get_user_listings(test_data['user_id'], active_only=False)
        
        if saved_listings:
            latest_listing = saved_listings[0]  # Pegar o mais recente
            print(f"📊 Anúncio recuperado: {latest_listing}")
            
            # Verificar algumas colunas importantes
            checks = [
                ('price_per_night', test_data['price_per_night']),
                ('rating', test_data['rating']),
                ('is_beachfront', test_data['is_beachfront']),
                ('host_name', test_data['host_name'])
            ]
            
            for field, expected_value in checks:
                actual_value = latest_listing.get(field)
                if actual_value == expected_value:
                    print(f"✅ {field}: {actual_value} (correto)")
                else:
                    print(f"⚠️ {field}: esperado {expected_value}, obtido {actual_value}")
        
        return listing_id
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_extract_and_save():
    """Testa a função extract_and_save_listing"""
    
    print("\n🧪 Testando função extract_and_save_listing...")
    
    try:
        db = get_database()
        if not db:
            print("❌ Erro: Não foi possível conectar ao banco de dados")
            return
        
        # Dados simulados do scraper
        scraper_data = {
            'title': 'Apartamento Moderno - Ipanema',
            'property_type': 'Apartamento',
            'max_guests': 4,
            'bedrooms': 2,
            'bathrooms': 1,
            'price_per_night': 180.00,
            'rating': 4.6,
            'reviews': 89,
            'municipality': 'Rio de Janeiro',
            'is_beachfront': True,
            'superhost': False,
            'instant_book': True
        }
        
        url = 'https://www.airbnb.com.br/rooms/extract_test456'
        user_id = 1
        
        listing_id = db.extract_and_save_listing(user_id, url, scraper_data)
        
        print(f"✅ Anúncio extraído e salvo com sucesso! ID: {listing_id}")
        
        return listing_id
        
    except Exception as e:
        print(f"❌ Erro no teste de extração: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Iniciando testes de salvamento completo...\n")
    
    # Teste 1: Salvamento direto
    listing_id_1 = test_save_complete_listing()
    
    # Teste 2: Função de extração
    listing_id_2 = test_extract_and_save()
    
    print("\n📋 Resumo dos testes:")
    print(f"- Teste salvamento direto: {'✅ Sucesso' if listing_id_1 else '❌ Falhou'}")
    print(f"- Teste extração e salvamento: {'✅ Sucesso' if listing_id_2 else '❌ Falhou'}")
    
    if listing_id_1 and listing_id_2:
        print("\n🎉 Todos os testes passaram! O sistema está salvando dados completos.")
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os logs acima.")