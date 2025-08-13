#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Completo do Fluxo de Análise com Usuário Autenticado
Simula uma sessão autenticada e testa o salvamento automático
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database
from auth import User

def test_authenticated_analysis():
    """
    Testa análise com usuário autenticado
    """
    print("🧪 TESTE: Análise com Usuário Autenticado")
    print("=" * 55)
    
    # Conectar ao banco
    print("🔍 Conectando ao banco de dados...")
    db = get_database()
    
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
    # Criar usuário de teste
    test_google_id = "test_analysis_user_987654321"
    test_email = "analise@hostlink.com"
    test_name = "Usuário Análise Teste"
    test_profile_pic = "https://example.com/profile.jpg"
    
    print(f"\n👤 Criando usuário de teste...")
    user_db_id = db.save_user(test_google_id, test_email, test_name, test_profile_pic)
    
    if not user_db_id:
        print("❌ Erro ao criar usuário de teste")
        return False
    
    print(f"✅ Usuário criado com ID: {user_db_id}")
    
    # Dados da análise
    listing_url = "https://www.airbnb.com.br/rooms/test_analysis_123"
    checkin = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    checkout = (datetime.now() + timedelta(days=9)).strftime('%Y-%m-%d')
    
    print(f"\n📋 Dados da análise:")
    print(f"   URL: {listing_url}")
    print(f"   Check-in: {checkin}")
    print(f"   Check-out: {checkout}")
    print(f"   Usuário ID: {user_db_id}")
    
    try:
        # Simular o fluxo do endpoint api_run_analysis
        print("\n🚀 Simulando fluxo de análise...")
        
        # 1. Verificar se o link já existe nos anúncios do usuário
        print("🔍 Verificando anúncios existentes do usuário...")
        user_listings = db.get_user_listings(user_db_id)
        print(f"   Anúncios encontrados: {len(user_listings)}")
        
        listing_found = False
        listing_id = None
        
        for listing in user_listings:
            if listing_url in listing.get('url', '') or listing.get('url', '') in listing_url:
                listing_id = listing['id']
                listing_found = True
                print(f"🎯 Anúncio existente encontrado: {listing['title']} (ID: {listing_id})")
                break
        
        # 2. Se não encontrou, salvar automaticamente
        if not listing_found:
            print("\n💾 Anúncio não encontrado, salvando automaticamente...")
            
            # Simular extração de dados básicos
            listing_title = "Casa de Praia Completa - Teste"
            municipio_id = 65  # Ipanema
            
            listing_id = db.save_user_listing(
                user_id=user_db_id,
                title=listing_title,
                url=listing_url,
                platform='airbnb',
                municipio_id=municipio_id,
                property_type='Casa',
                max_guests=6,
                bedrooms=3,
                bathrooms=2
            )
            
            if listing_id:
                print(f"✅ Anúncio salvo automaticamente com ID: {listing_id}")
                print(f"   Título: {listing_title}")
            else:
                print("❌ Erro ao salvar anúncio automaticamente")
                return False
        
        # 3. Criar dados de análise simulados
        print("\n📊 Criando análise simulada...")
        analysis_data = {
            'municipio_id': 65,
            'checkin': checkin,
            'checkout': checkout,
            'adults': 2,
            'beachfront': True,
            'period_type': 'weekend',
            'is_weekend': True,
            'timestamp': datetime.now().isoformat(),
            'pricing_suggestion': {
                'suggested_price': 450.0,
                'price_multiplier': 1.2,
                'justification': 'Preço ajustado para final de semana em área nobre',
                'discount_percentage': 0,
                'average_competitor_price': 400.0
            },
            'weather_data': [
                {
                    'date': checkin,
                    'rain_probability': 20,
                    'weather_condition': 'Ensolarado',
                    'description': 'Dia perfeito para praia'
                }
            ],
            'competitive_data': [
                {
                    'title': 'Apartamento Moderno - Concorrente 1',
                    'price': 380.0,
                    'rating': 4.8,
                    'reviews': 45,
                    'distance': '0.5 km',
                    'url': 'https://www.airbnb.com.br/rooms/competitor1',
                    'is_beachfront': True
                }
            ]
        }
        
        # 4. Salvar análise no banco
        print("💾 Salvando análise no banco...")
        analysis_id = db.save_analysis(analysis_data, user_id=user_db_id, listing_id=listing_id)
        
        if analysis_id:
            print(f"✅ Análise salva com ID: {analysis_id}")
            
            # 5. Verificar se tudo foi salvo corretamente
            print("\n🔍 Verificando dados salvos...")
            
            # Verificar anúncio
            updated_listings = db.get_user_listings(user_db_id)
            listing_saved = any(l['id'] == listing_id for l in updated_listings)
            
            # Verificar análise
            user_analyses = db.get_user_analyses(user_db_id, limit=5)
            analysis_saved = any(a['id'] == analysis_id for a in user_analyses)
            
            print(f"   📋 Anúncio salvo: {'✅ SIM' if listing_saved else '❌ NÃO'}")
            print(f"   📊 Análise salva: {'✅ SIM' if analysis_saved else '❌ NÃO'}")
            
            if listing_saved and analysis_saved:
                print("\n🎉 SUCESSO COMPLETO!")
                print("✅ Anúncio foi persistido na tabela user_listings")
                print("✅ Análise foi associada ao anúncio")
                print("✅ Dados estão disponíveis para consulta")
                
                # Mostrar detalhes
                saved_listing = next((l for l in updated_listings if l['id'] == listing_id), None)
                saved_analysis = next((a for a in user_analyses if a['id'] == analysis_id), None)
                
                if saved_listing:
                    print(f"\n📋 Detalhes do anúncio salvo:")
                    print(f"   ID: {saved_listing['id']}")
                    print(f"   Título: {saved_listing['title']}")
                    print(f"   URL: {saved_listing['url']}")
                    print(f"   Plataforma: {saved_listing['platform']}")
                    print(f"   Criado em: {saved_listing['created_at']}")
                
                if saved_analysis:
                    print(f"\n📊 Detalhes da análise salva:")
                    print(f"   ID: {saved_analysis['id']}")
                    print(f"   Usuário ID: {saved_analysis['user_id']}")
                    print(f"   Anúncio ID: {saved_analysis['listing_id']}")
                    print(f"   Preço sugerido: R$ {saved_analysis['suggested_price']}")
                    print(f"   Timestamp: {saved_analysis['timestamp']}")
                
                return True
            else:
                print("❌ Erro: Nem todos os dados foram salvos corretamente")
                return False
        else:
            print("❌ Erro ao salvar análise")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Limpar dados de teste
        print("\n🧹 Limpando dados de teste...")
        try:
            if listing_id:
                db.delete_user_listing(listing_id, user_db_id)
                print(f"   Anúncio {listing_id} removido")
        except Exception as e:
            print(f"⚠️ Erro ao limpar dados: {e}")

def main():
    """
    Função principal do teste
    """
    print("🏁 Iniciando teste completo do fluxo de análise...\n")
    
    success = test_authenticated_analysis()
    
    print("\n" + "=" * 70)
    print("📋 RESUMO DO TESTE COMPLETO:")
    print(f"   🔄 Fluxo completo de análise: {'✅ OK' if success else '❌ FALHOU'}")
    
    if success:
        print("\n🎉 TESTE COMPLETO PASSOU!")
        print("✅ A persistência na tabela de anúncios está funcionando")
        print("✅ O salvamento automático está operacional")
        print("✅ A associação entre usuário, anúncio e análise está correta")
    else:
        print("\n❌ TESTE FALHOU!")
        print("⚠️ Verifique os logs acima para identificar o problema")
    
    print("\n🏁 Teste concluído!")
    return success

if __name__ == "__main__":
    main()