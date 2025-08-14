#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de upload de imagem e verificação no banco de dados
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database

def test_image_upload_flow():
    """
    Testa o fluxo completo de upload de imagem
    """
    print("🧪 TESTE: Fluxo de upload de imagem")
    print("=" * 40)
    
    # Conectar ao banco
    print("🔗 Conectando ao banco de dados...")
    db = get_database()
    
    if not db:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
    try:
        # Buscar um anúncio existente para testar
        print("\n🏠 Buscando anúncios existentes...")
        listings_result = db.supabase.table('user_listings').select('id, title, image_url, user_id').limit(1).execute()
        
        if not listings_result.data:
            print("❌ Nenhum anúncio encontrado para teste")
            return False
        
        listing = listings_result.data[0]
        listing_id = listing['id']
        
        print(f"📋 Testando com anúncio ID: {listing_id}")
        print(f"   📝 Título: {listing['title'][:50]}...")
        print(f"   🖼️ Image URL atual: {listing.get('image_url', 'None')}")
        
        # Simular upload de uma nova imagem
        test_image_url = "static/uploads/test-image-123.jpg"
        
        print(f"\n🔄 Simulando atualização com nova imagem: {test_image_url}")
        
        # Atualizar o anúncio com nova imagem
        update_data = {
            'image_url': test_image_url,
            'updated_at': datetime.now().isoformat()
        }
        
        success = db.update_user_listing(listing_id, **update_data)
        
        if success:
            print("✅ Atualização realizada com sucesso")
            
            # Verificar se a atualização foi salva
            print("\n🔍 Verificando se a imagem foi salva...")
            updated_result = db.supabase.table('user_listings').select('id, image_url').eq('id', listing_id).execute()
            
            if updated_result.data:
                updated_listing = updated_result.data[0]
                saved_image_url = updated_listing.get('image_url')
                
                print(f"🖼️ Image URL salva: {saved_image_url}")
                
                if saved_image_url == test_image_url:
                    print("✅ SUCESSO: Imagem foi salva corretamente no banco!")
                    
                    # Reverter para o estado original
                    print("\n🔄 Revertendo para estado original...")
                    revert_data = {
                        'image_url': listing.get('image_url'),
                        'updated_at': datetime.now().isoformat()
                    }
                    db.update_user_listing(listing_id, **revert_data)
                    print("✅ Estado original restaurado")
                    
                    return True
                else:
                    print(f"❌ ERRO: Imagem não foi salva corretamente. Esperado: {test_image_url}, Encontrado: {saved_image_url}")
                    return False
            else:
                print("❌ ERRO: Não foi possível verificar a atualização")
                return False
        else:
            print("❌ ERRO: Falha na atualização")
            return False
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Função principal
    """
    success = test_image_upload_flow()
    
    if success:
        print("\n✅ Teste concluído com sucesso!")
        print("💡 O problema pode estar no frontend ou no processo de upload")
    else:
        print("\n❌ Teste falhou!")
        print("💡 O problema está no backend/banco de dados")
    
    print("🏁 Teste finalizado!")

if __name__ == "__main__":
    main()