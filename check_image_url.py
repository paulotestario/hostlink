#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificação específica do campo image_url na tabela user_listings
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database

def check_image_url_field():
    """
    Verifica especificamente o campo image_url nos anúncios
    """
    print("🔍 VERIFICAÇÃO: Campo image_url na tabela user_listings")
    print("=" * 55)
    
    # Conectar ao banco
    print("🔗 Conectando ao banco de dados...")
    db = get_database()
    
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
    try:
        # Buscar todos os anúncios com foco no image_url
        print("\n🏠 Verificando campo image_url em todos os anúncios...")
        listings_result = db.supabase.table('user_listings').select('id, title, image_url, user_id').execute()
        listings = listings_result.data
        
        print(f"📊 Total de anúncios encontrados: {len(listings)}")
        
        for listing in listings:
            print(f"\n📋 Anúncio ID: {listing['id']}")
            print(f"   📝 Título: {listing['title'][:50]}...")
            print(f"   👤 Usuário ID: {listing['user_id']}")
            print(f"   🖼️ Image URL: {listing.get('image_url', 'CAMPO NÃO ENCONTRADO')}")
            
            # Verificar se o campo existe
            if 'image_url' in listing:
                if listing['image_url']:
                    print(f"   ✅ Campo image_url presente com valor: {listing['image_url']}")
                else:
                    print(f"   ⚠️ Campo image_url presente mas vazio/null")
            else:
                print(f"   ❌ Campo image_url NÃO EXISTE na estrutura")
        
        # Testar uma busca específica de um anúncio
        if listings:
            test_id = listings[0]['id']
            print(f"\n🧪 Teste específico - Buscando anúncio ID {test_id}...")
            single_result = db.supabase.table('user_listings').select('*').eq('id', test_id).execute()
            if single_result.data:
                single_listing = single_result.data[0]
                print(f"📋 Campos disponíveis: {list(single_listing.keys())}")
                print(f"🖼️ Image URL específico: {single_listing.get('image_url', 'NÃO ENCONTRADO')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante verificação: {e}")
        return False

def main():
    """
    Função principal
    """
    success = check_image_url_field()
    
    if success:
        print("\n✅ Verificação concluída com sucesso!")
    else:
        print("\n❌ Verificação falhou!")
    
    print("🏁 Verificação finalizada!")

if __name__ == "__main__":
    main()