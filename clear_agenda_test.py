#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpar dados de teste da agenda
"""

import os
from dotenv import load_dotenv
from database import get_database

load_dotenv()

def clear_test_data():
    """Limpa os dados de teste da agenda"""
    try:
        db = get_database()
        print("✅ Conectado ao banco de dados")
        
        # Limpar tabela de disponibilidade
        try:
            result = db.supabase.table('listing_availability').delete().neq('id', 0).execute()
            print(f"✅ Removidos registros de disponibilidade")
        except Exception as e:
            print(f"⚠️ Erro ao limpar disponibilidade: {e}")
            
        # Limpar tabela de reservas
        try:
            result = db.supabase.table('listing_bookings').delete().neq('id', 0).execute()
            print(f"✅ Removidos registros de reservas")
        except Exception as e:
            print(f"⚠️ Erro ao limpar reservas: {e}")
            
        print("\n🎉 Dados de teste removidos com sucesso!")
        print("📋 A agenda agora mostrará o calendário vazio com mensagem informativa.")
        return True
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Limpando dados de teste da agenda...")
    clear_test_data()
    print("\n📋 Processo concluído!")