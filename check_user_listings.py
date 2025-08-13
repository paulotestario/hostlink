#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificação da Tabela user_listings
Verifica se há dados na tabela e como estão estruturados
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database

def check_user_listings():
    """
    Verifica o conteúdo da tabela user_listings
    """
    print("🔍 VERIFICAÇÃO: Tabela user_listings")
    print("=" * 45)
    
    # Conectar ao banco
    print("🔗 Conectando ao banco de dados...")
    db = get_database()
    
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
    try:
        # Verificar todos os usuários
        print("\n👥 Verificando usuários cadastrados...")
        users_result = db.supabase.table('users').select('*').execute()
        users = users_result.data
        
        print(f"📊 Total de usuários: {len(users)}")
        for user in users:
            print(f"   - ID: {user['id']}, Nome: {user['name']}, Email: {user['email']}")
        
        # Verificar todos os anúncios
        print("\n🏠 Verificando anúncios cadastrados...")
        listings_result = db.supabase.table('user_listings').select('*').execute()
        listings = listings_result.data
        
        print(f"📊 Total de anúncios: {len(listings)}")
        
        if listings:
            for listing in listings:
                print(f"\n📋 Anúncio ID: {listing['id']}")
                print(f"   👤 Usuário ID: {listing['user_id']}")
                print(f"   📝 Título: {listing['title']}")
                print(f"   🔗 URL: {listing['url']}")
                print(f"   🏢 Plataforma: {listing['platform']}")
                print(f"   🏙️ Município ID: {listing.get('municipio_id', 'N/A')}")
                print(f"   ✅ Ativo: {listing['is_active']}")
                print(f"   📅 Criado em: {listing['created_at']}")
        else:
            print("⚠️ Nenhum anúncio encontrado na tabela user_listings")
        
        # Verificar análises
        print("\n📊 Verificando análises cadastradas...")
        analyses_result = db.supabase.table('analyses').select('*').execute()
        analyses = analyses_result.data
        
        print(f"📊 Total de análises: {len(analyses)}")
        
        if analyses:
            for analysis in analyses[-5:]:  # Mostrar últimas 5
                print(f"\n📈 Análise ID: {analysis['id']}")
                print(f"   👤 Usuário ID: {analysis.get('user_id', 'N/A')}")
                print(f"   🏠 Anúncio ID: {analysis.get('listing_id', 'N/A')}")
                print(f"   🏙️ Município ID: {analysis.get('municipio_id', 'N/A')}")
                print(f"   💰 Preço sugerido: R$ {analysis.get('suggested_price', 'N/A')}")
                print(f"   📅 Timestamp: {analysis.get('timestamp', 'N/A')}")
        
        # Verificar função get_user_listings para usuários específicos
        print("\n🔍 Testando get_user_listings para cada usuário...")
        for user in users:
            user_id = user['id']
            user_listings = db.get_user_listings(user_id)
            print(f"   👤 Usuário {user_id} ({user['name']}): {len(user_listings)} anúncios")
            
            for listing in user_listings:
                print(f"      - {listing['title']} (ID: {listing['id']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante verificação: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Função principal
    """
    print("🏁 Iniciando verificação da tabela user_listings...\n")
    
    success = check_user_listings()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Verificação concluída com sucesso!")
    else:
        print("❌ Erro durante a verificação!")
    
    print("🏁 Verificação finalizada!")
    return success

if __name__ == "__main__":
    main()