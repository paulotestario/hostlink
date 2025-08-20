#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import get_database

def check_table_structure():
    """Verificar estrutura da tabela listing_bookings"""
    db = get_database()
    
    print("🔍 Verificando estrutura da tabela listing_bookings...")
    
    try:
        # Buscar uma reserva existente para ver as colunas
        result = db.supabase.table('listing_bookings').select('*').limit(1).execute()
        
        if result.data:
            print("\n✅ Colunas disponíveis na tabela listing_bookings:")
            columns = list(result.data[0].keys())
            for i, column in enumerate(columns, 1):
                print(f"   {i:2d}. {column}")
            
            print("\n📊 Exemplo de dados:")
            for key, value in result.data[0].items():
                print(f"   {key}: {value}")
        else:
            print("❌ Nenhum dado encontrado na tabela")
            
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")

if __name__ == '__main__':
    check_table_structure()