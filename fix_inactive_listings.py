#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correção de Anúncios Inativos
Ativa os anúncios que estão marcados como inativos
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database

def fix_inactive_listings():
    """
    Ativa anúncios que estão marcados como inativos
    """
    print("🔧 CORREÇÃO: Ativando Anúncios Inativos")
    print("=" * 45)
    
    # Conectar ao banco
    print("🔗 Conectando ao banco de dados...")
    db = get_database()
    
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
    try:
        # Buscar anúncios inativos
        print("\n🔍 Buscando anúncios inativos...")
        inactive_result = db.supabase.table('user_listings').select('*').eq('is_active', False).execute()
        inactive_listings = inactive_result.data
        
        print(f"📊 Anúncios inativos encontrados: {len(inactive_listings)}")
        
        if not inactive_listings:
            print("✅ Nenhum anúncio inativo encontrado!")
            return True
        
        # Mostrar anúncios inativos
        for listing in inactive_listings:
            print(f"\n📋 Anúncio ID: {listing['id']}")
            print(f"   👤 Usuário ID: {listing['user_id']}")
            print(f"   📝 Título: {listing['title']}")
            print(f"   🔗 URL: {listing['url']}")
            print(f"   📅 Criado em: {listing['created_at']}")
        
        # Confirmar ativação
        print(f"\n🚀 Ativando {len(inactive_listings)} anúncios...")
        
        activated_count = 0
        for listing in inactive_listings:
            try:
                # Ativar o anúncio
                update_result = db.supabase.table('user_listings').update({
                    'is_active': True,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', listing['id']).execute()
                
                if update_result.data:
                    print(f"   ✅ Anúncio {listing['id']} ativado: {listing['title']}")
                    activated_count += 1
                else:
                    print(f"   ❌ Erro ao ativar anúncio {listing['id']}")
                    
            except Exception as e:
                print(f"   ❌ Erro ao ativar anúncio {listing['id']}: {e}")
        
        print(f"\n📊 Resumo da ativação:")
        print(f"   🎯 Anúncios processados: {len(inactive_listings)}")
        print(f"   ✅ Anúncios ativados: {activated_count}")
        print(f"   ❌ Falhas: {len(inactive_listings) - activated_count}")
        
        # Verificar resultado
        print("\n🔍 Verificando resultado...")
        for user_id in set(listing['user_id'] for listing in inactive_listings):
            user_listings = db.get_user_listings(user_id, active_only=True)
            print(f"   👤 Usuário {user_id}: {len(user_listings)} anúncios ativos")
            
            for listing in user_listings:
                print(f"      - {listing['title']} (ID: {listing['id']})")
        
        return activated_count > 0
        
    except Exception as e:
        print(f"❌ Erro durante correção: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Função principal
    """
    print("🏁 Iniciando correção de anúncios inativos...\n")
    
    success = fix_inactive_listings()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Correção concluída com sucesso!")
        print("🎉 Os anúncios agora devem aparecer na interface!")
    else:
        print("❌ Erro durante a correção!")
    
    print("\n💡 Próximos passos:")
    print("   1. Acesse http://localhost:5000/perfil")
    print("   2. Faça login com sua conta Google")
    print("   3. Verifique se os anúncios aparecem em 'Meus Anúncios'")
    
    print("\n🏁 Correção finalizada!")
    return success

if __name__ == "__main__":
    main()