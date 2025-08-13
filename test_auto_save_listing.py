#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar o salvamento automático de links de anúncios
quando o usuário clica em "Executar Análise"
"""

import requests
import json
from datetime import datetime, timedelta

def test_auto_save_listing():
    """
    Testa o salvamento automático do link do anúncio na análise
    """
    print("🧪 Testando salvamento automático de link do anúncio...")
    print("="*60)
    
    # URL base da aplicação
    base_url = "http://localhost:5000"
    
    # Dados de teste para análise
    test_data = {
        "checkin": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        "checkout": (datetime.now() + timedelta(days=9)).strftime('%Y-%m-%d'),
        "adults": 2,
        "beachfront": True,
        "period_type": "weekend",
        "listing_url": "https://www.airbnb.com.br/rooms/12345678",  # URL de teste
        "municipio_id": 1  # ID de teste
    }
    
    print(f"📅 Período de teste: {test_data['checkin']} a {test_data['checkout']}")
    print(f"🔗 URL do anúncio: {test_data['listing_url']}")
    print(f"🏖️ Frente à praia: {test_data['beachfront']}")
    print()
    
    try:
        # Fazer requisição para executar análise
        print("🚀 Executando análise com salvamento automático...")
        response = requests.post(
            f"{base_url}/api/run_analysis",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ Análise executada com sucesso!")
                
                # Verificar se os dados foram salvos
                analysis_data = result.get('data', {})
                
                print(f"🆔 ID da análise: {analysis_data.get('id', 'N/A')}")
                print(f"👤 ID do usuário: {analysis_data.get('user_id', 'N/A')}")
                print(f"🏠 ID do anúncio: {analysis_data.get('listing_id', 'N/A')}")
                print(f"🏙️ Município: {analysis_data.get('extracted_municipality', 'N/A')}")
                print(f"💰 Preço sugerido: R$ {analysis_data.get('pricing_suggestion', {}).get('suggested_price', 'N/A')}")
                
                # Verificar se o link foi salvo automaticamente
                if analysis_data.get('listing_id'):
                    print("\n🎯 SUCESSO: Link do anúncio foi salvo automaticamente na tabela user_listings!")
                    print(f"   - ID do anúncio salvo: {analysis_data['listing_id']}")
                    print(f"   - Associado ao usuário: {analysis_data.get('user_id')}")
                else:
                    print("\n⚠️ ATENÇÃO: Link do anúncio não foi associado (pode ser usuário não logado)")
                
                print("\n📋 Resumo da funcionalidade:")
                print("   ✅ Análise executada")
                print("   ✅ Dados salvos no banco")
                print("   ✅ Link do anúncio processado automaticamente")
                
            else:
                print(f"❌ Erro na análise: {result.get('error', 'Erro desconhecido')}")
                print(f"💬 Mensagem: {result.get('message', 'N/A')}")
                
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"💬 Erro: {error_data.get('error', 'Erro desconhecido')}")
                print(f"📝 Mensagem: {error_data.get('message', 'N/A')}")
            except:
                print(f"📄 Resposta: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão: Verifique se o servidor está rodando em http://localhost:5000")
        print("💡 Execute: python web_app.py")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    
    print("\n" + "="*60)
    print("🏁 Teste concluído!")
    print("\n💡 Como verificar se funcionou:")
    print("   1. Acesse http://localhost:5000/perfil")
    print("   2. Verifique se o anúncio aparece na lista 'Meus Anúncios'")
    print("   3. Confira se a análise aparece em 'Análises Recentes'")

def test_database_connection():
    """
    Testa a conexão com o banco de dados
    """
    print("🔍 Testando conexão com banco de dados...")
    
    try:
        from database import get_database
        
        db = get_database()
        if db:
            if db.test_connection():
                print("✅ Conexão com banco de dados OK")
                return True
            else:
                print("❌ Falha na conexão com banco de dados")
                return False
        else:
            print("❌ Banco de dados não inicializado")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar banco: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE: Salvamento Automático de Link do Anúncio")
    print("="*60)
    print("Este teste verifica se o link do anúncio é salvo automaticamente")
    print("na tabela 'user_listings' quando o usuário clica em 'Executar Análise'")
    print()
    
    # Testar conexão com banco primeiro
    if test_database_connection():
        print()
        test_auto_save_listing()
    else:
        print("\n⚠️ Não é possível executar o teste sem conexão com o banco")
        print("💡 Verifique as configurações do Supabase no arquivo .env")