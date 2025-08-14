#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar se as datas de disponibilidade ficam verdes
"""

import os
import sys
from datetime import datetime, timedelta

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database

def add_green_availability():
    """Adiciona algumas datas de disponibilidade para testar se ficam verdes"""
    try:
        print("🔄 Conectando ao banco de dados...")
        db = get_database()
        
        # Buscar listings existentes
        print("📋 Buscando listings...")
        result = db.supabase.table('user_listings').select('id, user_id, title').execute()
        
        if not result.data:
            print("❌ Nenhum listing encontrado")
            return False
            
        listing = result.data[0]
        listing_id = listing['id']
        user_id = listing['user_id']
        
        print(f"✅ Usando listing: {listing['title']} (ID: {listing_id})")
        
        # Adicionar disponibilidade para os próximos 7 dias
        today = datetime.now()
        
        for i in range(7):
            date = today + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Preço variável
            price = 150 + (i * 10)  # R$ 150, 160, 170, etc.
            
            success = db.save_listing_availability(
                listing_id=listing_id,
                user_id=user_id,
                date=date_str,
                is_available=True,  # SEMPRE TRUE para ficar verde
                price_per_night=price,
                minimum_nights=1,
                maximum_nights=3,
                notes="Teste - deve aparecer verde"
            )
            
            if success:
                print(f"✅ {date_str}: R$ {price}/noite - VERDE")
            else:
                print(f"❌ Erro ao salvar {date_str}")
                
        print("\n🎉 Disponibilidade adicionada com sucesso!")
        print("🌐 Acesse http://localhost:5000/hosting e abra a agenda")
        print("📅 As datas devem aparecer em VERDE com os preços")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testando disponibilidade verde...")
    add_green_availability()
    print("\n📋 Teste concluído!")