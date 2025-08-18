#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_database

def check_listings():
    """Verifica os dados dos anúncios"""
    try:
        db = get_database()
        
        print("🔍 Verificando anúncios...\n")
        
        listings = db.get_all_public_listings()
        print(f"📊 Total de anúncios: {len(listings)}\n")
        
        for i, listing in enumerate(listings[:5]):
            print(f"📋 Anúncio {i+1}:")
            print(f"   ID: {listing['id']}")
            print(f"   Título: {listing.get('title', 'N/A')}")
            print(f"   Preço por noite: {listing.get('price_per_night', 'N/A')}")
            print(f"   Host ID: {listing.get('user_id', 'N/A')}")
            print(f"   Ativo: {listing.get('is_active', 'N/A')}")
            print()
            
        # Atualizar um anúncio com preço se necessário
        if listings and listings[0].get('price_per_night') is None:
            print("🔧 Atualizando preço do primeiro anúncio...")
            listing_id = listings[0]['id']
            
            # Atualizar com um preço de teste
            success = db.update_user_listing(listing_id, price_per_night=150.0)
            if success:
                print(f"✅ Preço atualizado para R$ 150,00 no anúncio {listing_id}")
            else:
                print(f"❌ Erro ao atualizar preço do anúncio {listing_id}")
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_listings()