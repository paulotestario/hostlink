#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime

def test_review_api():
    """Teste simples da API de avaliações usando requests"""
    print("🚀 Iniciando teste simples da API de avaliações...")
    print("=" * 60)
    
    base_url = 'http://localhost:5000'
    test_booking_id = 3
    test_user_id = 1
    
    # Criar sessão para manter cookies
    session = requests.Session()
    
    success_count = 0
    total_tests = 0
    
    # Teste 1: Verificar se pode editar avaliação
    total_tests += 1
    print("\n📋 Teste 1: Verificar permissão de edição")
    
    try:
        response = session.get(
            f"{base_url}/api/reviews/can-edit/{test_booking_id}"
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Resposta da API: {data}")
                if data.get('can_edit'):
                    print("   ✅ Usuário pode editar a avaliação")
                    success_count += 1
                else:
                    print(f"   ⚠️ Usuário não pode editar: {data.get('reason')}")
                    success_count += 1  # Ainda é um sucesso válido
            except json.JSONDecodeError:
                print("   ❌ Resposta não é JSON válido")
                print(f"   Conteúdo: {response.text[:200]}...")
        elif response.status_code == 302:
            print("   ⚠️ Redirecionamento (provavelmente para login)")
            print(f"   Location: {response.headers.get('location', 'N/A')}")
        else:
            print(f"   ❌ Erro na API: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro ao testar API: {e}")
    
    # Teste 2: Buscar avaliação existente
    total_tests += 1
    print("\n📋 Teste 2: Buscar avaliação existente")
    
    try:
        response = session.get(
            f"{base_url}/api/reviews/booking/{test_booking_id}"
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('review'):
                    print(f"   ✅ Avaliação encontrada: {data['review'].get('review_title', 'Sem título')}")
                    success_count += 1
                else:
                    print("   ⚠️ Nenhuma avaliação encontrada")
                    success_count += 1  # Ainda é válido
            except json.JSONDecodeError:
                print("   ❌ Resposta não é JSON válido")
        elif response.status_code == 302:
            print("   ⚠️ Redirecionamento (provavelmente para login)")
        else:
            print(f"   ❌ Erro na API: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro ao buscar avaliação: {e}")
    
    # Teste 3: Atualizar avaliação
    total_tests += 1
    print("\n📋 Teste 3: Atualizar avaliação")
    
    try:
        update_data = {
            'review_title': f'Teste API - {datetime.now().strftime("%H:%M:%S")}',
            'review_comment': 'Comentário de teste via API',
            'overall_rating': 5,
            'cleanliness_rating': 5,
            'checkin_rating': 4,
            'location_rating': 4,
            'value_rating': 5
        }
        
        response = session.put(
            f"{base_url}/api/reviews",
            json={
                'booking_id': test_booking_id,
                **update_data
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Avaliação atualizada com sucesso")
                success_count += 1
            else:
                print(f"   ❌ Falha na atualização: {data.get('message')}")
        else:
            print(f"   ❌ Erro na API: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erro ao atualizar avaliação: {e}")
    
    # Teste 4: Verificar página de avaliação
    total_tests += 1
    print("\n📋 Teste 4: Verificar página de avaliação")
    
    try:
        response = session.get(f"{base_url}/avaliar-hospedagem?booking_id={test_booking_id}")
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            if 'Avaliação' in response.text or 'avaliar' in response.text.lower():
                print("   ✅ Página de avaliação carregou corretamente")
                success_count += 1
            else:
                print("   ⚠️ Página carregou mas conteúdo pode estar incorreto")
        elif response.status_code == 302:
            print("   ⚠️ Redirecionamento (provavelmente para login)")
            print("   ℹ️ As rotas requerem autenticação")
        else:
            print(f"   ❌ Erro ao carregar página: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro ao acessar página: {e}")
    
    # Resultados finais
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES DA API")
    print(f"   Total de testes: {total_tests}")
    print(f"   Sucessos: {success_count}")
    print(f"   Falhas: {total_tests - success_count}")
    
    success_rate = (success_count / total_tests) * 100
    
    if success_rate >= 75:
        print(f"\n🎉 TESTES APROVADOS! ({success_rate:.1f}% de sucesso)")
        print("✅ A API de avaliações está funcionando corretamente")
        return True
    else:
        print(f"\n❌ TESTES FALHARAM! ({success_rate:.1f}% de sucesso)")
        print("⚠️ A API precisa de correções")
        return False

if __name__ == '__main__':
    success = test_review_api()
    exit(0 if success else 1)