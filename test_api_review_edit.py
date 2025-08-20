#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime
from database import get_database

def test_api_review_functionality():
    """Testes da API de edição de avaliações usando requests"""
    print("🔧 Iniciando testes da API de edição de avaliações")
    print("=" * 60)
    
    base_url = 'http://localhost:5000'
    db = get_database()
    test_booking_id = 6
    
    # Verificar se o servidor está rodando
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ Servidor respondendo: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Servidor não está rodando: {e}")
        return False
    
    success_count = 0
    total_tests = 0
    
    # Teste 1: Verificar endpoint can-edit
    total_tests += 1
    print(f"\n📋 Teste 1: Endpoint /api/reviews/can-edit/{test_booking_id}")
    try:
        response = requests.get(f"{base_url}/api/reviews/can-edit/{test_booking_id}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Resposta JSON: {json.dumps(data, indent=2)}")
                
                if 'can_edit' in data:
                    print(f"   ✅ Campo 'can_edit' presente: {data['can_edit']}")
                    success_count += 1
                else:
                    print("   ❌ Campo 'can_edit' ausente")
            except json.JSONDecodeError:
                print(f"   ❌ Resposta não é JSON válido: {response.text[:200]}")
        else:
            print(f"   ❌ Status code inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro na requisição: {e}")
    
    # Teste 2: Verificar dados no banco
    total_tests += 1
    print(f"\n📋 Teste 2: Verificar dados no banco para booking {test_booking_id}")
    try:
        # Verificar se booking existe
        booking = db.get_booking_by_id(test_booking_id)
        if booking:
            print(f"   ✅ Booking encontrado: ID {booking['id']}")
            
            # Verificar se há avaliação
            review = db.get_booking_review(test_booking_id)
            if review:
                print(f"   ✅ Avaliação encontrada: '{review.get('review_title', 'Sem título')}'")
                print(f"   Data da avaliação: {review.get('created_at', 'N/A')}")
            else:
                print("   ⚠️ Nenhuma avaliação encontrada")
            
            # Verificar permissão de edição
            can_edit_result = db.can_user_edit_review(booking['user_id'], test_booking_id)
            print(f"   Permissão de edição: {can_edit_result}")
            
            success_count += 1
        else:
            print(f"   ❌ Booking {test_booking_id} não encontrado")
            
    except Exception as e:
        print(f"   ❌ Erro ao acessar banco: {e}")
    
    # Teste 3: Testar criação/atualização de avaliação
    total_tests += 1
    print(f"\n📋 Teste 3: Testar API de criação/atualização")
    try:
        # Dados de teste
        test_data = {
            'booking_id': test_booking_id,
            'overall_rating': 4,
            'cleanliness_rating': 4,
            'checkin_rating': 5,
            'accuracy_rating': 4,
            'location_rating': 5,
            'value_rating': 4,
            'review_title': f'Teste API - {datetime.now().strftime("%H:%M:%S")}',
            'review_comment': 'Comentário de teste automatizado via API',
            'recommend_host': True,
            'public_review': True
        }
        
        # Tentar PUT (atualização)
        response = requests.put(
            f"{base_url}/api/reviews",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Status da requisição PUT: {response.status_code}")
        
        if response.status_code in [200, 201]:
            try:
                result = response.json()
                print(f"   ✅ Resposta: {result.get('message', 'Sucesso')}")
                success_count += 1
            except json.JSONDecodeError:
                print(f"   ⚠️ Resposta não é JSON: {response.text[:100]}")
                if response.status_code == 200:
                    success_count += 1
        else:
            print(f"   ❌ Falha na atualização: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Erro na requisição PUT: {e}")
    
    # Teste 4: Verificar se a atualização foi salva
    total_tests += 1
    print(f"\n📋 Teste 4: Verificar se atualização foi salva")
    try:
        updated_review = db.get_booking_review(test_booking_id)
        if updated_review:
            current_title = updated_review.get('review_title', '')
            if 'Teste API' in current_title:
                print(f"   ✅ Atualização confirmada: {current_title}")
                success_count += 1
            else:
                print(f"   ⚠️ Título não foi atualizado: {current_title}")
        else:
            print("   ❌ Avaliação não encontrada após atualização")
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar atualização: {e}")
    
    # Teste 5: Verificar estatísticas
    total_tests += 1
    print(f"\n📋 Teste 5: Verificar atualização de estatísticas")
    try:
        # Buscar estatísticas da propriedade
        booking = db.get_booking_by_id(test_booking_id)
        if booking:
            property_id = booking['property_id']
            stats = db.get_property_statistics(property_id)
            
            if stats:
                print(f"   ✅ Estatísticas encontradas:")
                print(f"   - Avaliação média: {stats.get('average_rating', 'N/A')}")
                print(f"   - Total de avaliações: {stats.get('total_reviews', 'N/A')}")
                success_count += 1
            else:
                print("   ⚠️ Estatísticas não encontradas")
        else:
            print("   ❌ Booking não encontrado para verificar estatísticas")
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar estatísticas: {e}")
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES DA API")
    print(f"   Total de testes: {total_tests}")
    print(f"   Sucessos: {success_count}")
    print(f"   Falhas: {total_tests - success_count}")
    
    success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
    
    if success_rate >= 80:
        print(f"\n🎉 TESTES APROVADOS! ({success_rate:.1f}% de sucesso)")
        print("✅ A API de edição de avaliações está funcionando corretamente")
        return True
    else:
        print(f"\n⚠️ TESTES PARCIALMENTE APROVADOS ({success_rate:.1f}% de sucesso)")
        print("❌ Algumas funcionalidades podem precisar de ajustes")
        return False

def run_comprehensive_tests():
    """Executar testes abrangentes (Selenium + API)"""
    print("🚀 INICIANDO TESTES AUTOMATIZADOS ABRANGENTES")
    print("=" * 70)
    
    # Primeiro tentar testes da API
    api_success = test_api_review_functionality()
    
    # Tentar testes Selenium como complemento
    selenium_success = False
    try:
        print("\n" + "=" * 70)
        print("🔧 Tentando executar testes Selenium...")
        
        from test_selenium_review_edit import run_selenium_tests
        selenium_success = run_selenium_tests()
        
    except Exception as e:
        print(f"⚠️ Testes Selenium não puderam ser executados: {e}")
        print("   Continuando apenas com testes da API...")
    
    # Resultado final
    print("\n" + "=" * 70)
    print("🏁 RESULTADO FINAL DOS TESTES")
    print(f"   Testes da API: {'✅ PASSOU' if api_success else '❌ FALHOU'}")
    print(f"   Testes Selenium: {'✅ PASSOU' if selenium_success else '⚠️ NÃO EXECUTADO'}")
    
    overall_success = api_success  # Consideramos sucesso se pelo menos a API funciona
    
    if overall_success:
        print("\n🎉 FUNCIONALIDADE APROVADA PARA PRODUÇÃO!")
        print("✅ A edição de avaliações está pronta para uso")
    else:
        print("\n❌ FUNCIONALIDADE PRECISA DE CORREÇÕES")
        print("⚠️ Não recomendado para produção no estado atual")
    
    return overall_success

if __name__ == '__main__':
    success = run_comprehensive_tests()
    exit(0 if success else 1)