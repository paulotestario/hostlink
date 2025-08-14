#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para popular a agenda com dados de teste
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import get_database

load_dotenv()

def populate_test_data():
    """Popula a agenda com dados de teste"""
    try:
        db = get_database()
        print("✅ Conectado ao banco de dados")
        
        # Obter anúncios existentes
        listings = db.supabase.table('user_listings').select('id, user_id, title').execute()
        
        if not listings.data:
            print("❌ Nenhum anúncio encontrado")
            return False
            
        print(f"📋 Encontrados {len(listings.data)} anúncios")
        
        # Para cada anúncio, criar disponibilidade para os próximos 30 dias
        for listing in listings.data:
            listing_id = listing['id']
            user_id = listing['user_id']
            title = listing['title'][:30]
            
            print(f"\n🏠 Criando disponibilidade para: {title}...")
            
            # Criar disponibilidade para os próximos 30 dias
            start_date = datetime.now()
            
            for i in range(30):
                current_date = start_date + timedelta(days=i)
                date_str = current_date.strftime('%Y-%m-%d')
                
                # Preço varia entre R$ 150-300 dependendo do dia
                base_price = 200
                if current_date.weekday() >= 5:  # Fim de semana
                    price = base_price + 50
                else:
                    price = base_price
                    
                # Adicionar variação aleatória
                price += (i % 10) * 10
                
                # Algumas datas ficam indisponíveis (simulando reservas)
                is_available = not (i % 7 == 0)  # A cada 7 dias fica indisponível
                
                try:
                    success = db.save_listing_availability(
                        listing_id=listing_id,
                        user_id=user_id,
                        date=date_str,
                        is_available=is_available,
                        price_per_night=price,
                        minimum_nights=1,
                        maximum_nights=7,
                        notes=f"Preço automático - {'Disponível' if is_available else 'Ocupado'}"
                    )
                    
                    if success:
                        status = "✅" if is_available else "❌"
                        print(f"   {status} {date_str}: R$ {price}/noite")
                    else:
                        print(f"   ⚠️ Erro ao salvar {date_str}")
                        
                except Exception as e:
                    print(f"   ❌ Erro em {date_str}: {e}")
                    
        print("\n🎉 Dados de teste criados com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Populando agenda com dados de teste...")
    populate_test_data()
    print("\n📋 Processo concluído!")