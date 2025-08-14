#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar se as tabelas da agenda existem no banco de dados
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def test_agenda_tables():
    """Testa se as tabelas da agenda existem no banco de dados"""
    try:
        # Conectar ao Supabase
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            print("❌ Variáveis de ambiente SUPABASE_URL ou SUPABASE_KEY não encontradas")
            return False
            
        supabase: Client = create_client(url, key)
        print("✅ Conectado ao Supabase")
        
        # Testar tabela listing_availability
        try:
            result = supabase.table('listing_availability').select('*').limit(1).execute()
            print(f"✅ Tabela 'listing_availability' existe - {len(result.data)} registros encontrados")
        except Exception as e:
            print(f"❌ Tabela 'listing_availability' não existe ou erro: {e}")
            
        # Testar tabela listing_bookings
        try:
            result = supabase.table('listing_bookings').select('*').limit(1).execute()
            print(f"✅ Tabela 'listing_bookings' existe - {len(result.data)} registros encontrados")
        except Exception as e:
            print(f"❌ Tabela 'listing_bookings' não existe ou erro: {e}")
            
        # Verificar se há anúncios cadastrados
        try:
            result = supabase.table('user_listings').select('id, title').limit(5).execute()
            print(f"✅ Encontrados {len(result.data)} anúncios cadastrados:")
            for listing in result.data:
                print(f"   - ID: {listing['id']}, Título: {listing['title'][:50]}...")
        except Exception as e:
            print(f"❌ Erro ao buscar anúncios: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testando tabelas da agenda...")
    test_agenda_tables()
    print("\n📋 Teste concluído!")