#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Direto de Salvamento na Tabela user_listings
Testa diretamente a função save_user_listing para verificar persistência
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database

def test_direct_save():
    """
    Testa o salvamento direto na tabela user_listings
    """
    print("🧪 TESTE DIRETO: Salvamento na Tabela user_listings")
    print("=" * 60)
    
    # Conectar ao banco
    print("🔍 Conectando ao banco de dados...")
    db = get_database()
    
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
    # Dados de teste
    test_data = {
        'user_id': 1,  # Assumindo que existe um usuário com ID 1
        'title': 'Teste de Salvamento Automático',
        'url': 'https://www.airbnb.com.br/rooms/test123456',
        'platform': 'airbnb',
        'municipio_id': 65,  # Ipanema
        'property_type': 'Apartamento',
        'max_guests': 4,
        'bedrooms': 2,
        'bathrooms': 1
    }
    
    print(f"📝 Dados de teste: {test_data}")
    print("\n🚀 Tentando salvar na tabela user_listings...")
    
    try:
        # Tentar salvar
        listing_id = db.save_user_listing(**test_data)
        
        if listing_id:
            print(f"✅ SUCESSO! Anúncio salvo com ID: {listing_id}")
            
            # Verificar se foi realmente salvo
            print("\n🔍 Verificando se foi salvo corretamente...")
            user_listings = db.get_user_listings(test_data['user_id'])
            
            found = False
            for listing in user_listings:
                if listing['id'] == listing_id:
                    found = True
                    print(f"✅ Anúncio encontrado na base de dados:")
                    print(f"   - ID: {listing['id']}")
                    print(f"   - Título: {listing['title']}")
                    print(f"   - URL: {listing['url']}")
                    print(f"   - Plataforma: {listing['platform']}")
                    print(f"   - Criado em: {listing['created_at']}")
                    break
            
            if not found:
                print("❌ ERRO: Anúncio não encontrado na base de dados")
                return False
            
            # Limpar dados de teste
            print("\n🧹 Limpando dados de teste...")
            success = db.delete_user_listing(listing_id, test_data['user_id'])
            if success:
                print("✅ Dados de teste removidos com sucesso")
            else:
                print("⚠️ Aviso: Não foi possível remover dados de teste")
            
            return True
            
        else:
            print("❌ ERRO: Função retornou None - não foi possível salvar")
            return False
            
    except Exception as e:
        print(f"❌ ERRO durante o salvamento: {e}")
        return False

def test_table_structure():
    """
    Testa a estrutura da tabela user_listings
    """
    print("\n🔍 TESTE: Estrutura da Tabela user_listings")
    print("=" * 60)
    
    db = get_database()
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco")
        return False
    
    try:
        # Tentar fazer uma consulta simples para verificar a estrutura
        result = db.supabase.table('user_listings').select('*').limit(1).execute()
        
        if result.data:
            print("✅ Tabela user_listings existe e é acessível")
            if len(result.data) > 0:
                print(f"📊 Campos disponíveis: {list(result.data[0].keys())}")
            else:
                print("📊 Tabela está vazia, mas estrutura é válida")
        else:
            print("⚠️ Tabela existe mas pode estar vazia")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura da tabela: {e}")
        return False

if __name__ == "__main__":
    print("🧪 INICIANDO TESTES DE PERSISTÊNCIA")
    print("=" * 60)
    
    # Teste 1: Estrutura da tabela
    structure_ok = test_table_structure()
    
    # Teste 2: Salvamento direto
    if structure_ok:
        save_ok = test_direct_save()
        
        print("\n" + "=" * 60)
        print("📋 RESUMO DOS TESTES:")
        print(f"   🏗️ Estrutura da tabela: {'✅ OK' if structure_ok else '❌ ERRO'}")
        print(f"   💾 Salvamento direto: {'✅ OK' if save_ok else '❌ ERRO'}")
        
        if structure_ok and save_ok:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print("✅ A persistência na tabela user_listings está funcionando")
        else:
            print("\n⚠️ ALGUNS TESTES FALHARAM")
            print("❌ Verifique a configuração do banco de dados")
    else:
        print("\n❌ Não foi possível executar teste de salvamento")
        print("❌ Problema na estrutura da tabela")
    
    print("\n🏁 Testes concluídos!")