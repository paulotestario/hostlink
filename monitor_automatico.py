#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor Automático de Preços Airbnb
Executa análise competitiva 2x ao dia e envia relatórios por email
"""

from airbnb_scraper import AirbnbClimateScraper
import sys
import os
from datetime import datetime

def configurar_email():
    """
    Configura as credenciais de email
    """
    print("📧 Configuração de Email")
    print("="*40)
    print("\n⚠️ IMPORTANTE: Para Gmail, use uma 'Senha de App' em vez da senha normal.")
    print("   Como criar: https://support.google.com/accounts/answer/185833")
    print("\n💡 Deixe em branco para usar configuração padrão (sem envio de email)\n")
    
    sender_email = input("📧 Email remetente (Gmail): ").strip()
    if not sender_email:
        return None
    
    sender_password = input("🔑 Senha de app do Gmail: ").strip()
    if not sender_password:
        return None
    
    recipient_email = input("📬 Email destinatário (padrão: paulotestario@gmail.com): ").strip()
    if not recipient_email:
        recipient_email = "paulotestario@gmail.com"
    
    return {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': sender_email,
        'sender_password': sender_password,
        'recipient_email': recipient_email
    }

def main():
    print("🏖️ Monitor Automático - Hotel Mont Blanc Itacuruçá")
    print("="*55)
    
    # Configurar email
    email_config = configurar_email()
    
    if not email_config:
        print("\n⚠️ Executando sem configuração de email (apenas console)")
        resposta = input("\nDeseja continuar? (s/n): ").lower()
        if resposta != 's':
            print("❌ Operação cancelada")
            return
    
    # Configurar se o anúncio é frente à praia
    print("\n🏖️ Configuração do Anúncio")
    print("="*30)
    
    while True:
        beachfront_input = input("Seu anúncio é frente à praia? (s/n): ").lower().strip()
        if beachfront_input in ['s', 'sim', 'y', 'yes']:
            my_listing_beachfront = True
            break
        elif beachfront_input in ['n', 'não', 'nao', 'no']:
            my_listing_beachfront = False
            break
        else:
            print("❌ Responda com 's' para sim ou 'n' para não")
    
    # Criar scraper
    scraper = AirbnbClimateScraper(email_config)
    
    print("\n🚀 Iniciando monitoramento automático...")
    print(f"📧 Relatórios serão enviados para: {email_config['recipient_email'] if email_config else 'Nenhum (apenas console)'}")
    print(f"🏖️ Anúncio frente à praia: {'Sim' if my_listing_beachfront else 'Não'}")
    
    # Iniciar monitoramento
    try:
        scraper.start_automated_monitoring(my_listing_beachfront)
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoramento interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro no monitoramento: {e}")
        print("💡 Verifique sua conexão com a internet e configurações de email")

def teste_analise():
    """
    Executa uma análise de teste sem monitoramento contínuo
    """
    print("🧪 Modo de Teste - Análise Única")
    print("="*35)
    
    # Configurar email (opcional para teste)
    email_config = configurar_email()
    
    # Configurar anúncio
    beachfront_input = input("\nSeu anúncio é frente à praia? (s/n): ").lower().strip()
    my_listing_beachfront = beachfront_input in ['s', 'sim', 'y', 'yes']
    
    # Criar scraper e executar análise
    scraper = AirbnbClimateScraper(email_config)
    
    # Usar próximo final de semana como exemplo
    from datetime import datetime, timedelta
    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0 and today.weekday() >= 4:
        days_until_friday = 7
    
    next_friday = today + timedelta(days=days_until_friday)
    next_sunday = next_friday + timedelta(days=2)
    
    checkin = next_friday.strftime('%Y-%m-%d')
    checkout = next_sunday.strftime('%Y-%m-%d')
    
    print(f"\n🔍 Executando análise de teste para {checkin} a {checkout}")
    
    try:
        result = scraper.run_competitive_analysis(checkin, checkout, my_listing_beachfront)
        
        print("\n✅ Análise de teste concluída com sucesso!")
        if result['email_sent']:
            print("📧 Email de teste enviado")
        else:
            print("📧 Email não enviado (verifique configurações)")
            
    except Exception as e:
        print(f"\n❌ Erro na análise de teste: {e}")

if __name__ == "__main__":
    print("\n🏖️ Sistema de Monitoramento Airbnb - Hotel Mont Blanc")
    print("="*60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--teste":
        teste_analise()
    else:
        print("\n📋 Escolha uma opção:")
        print("1. 🤖 Iniciar monitoramento automático (2x ao dia)")
        print("2. 🧪 Executar análise de teste (uma vez)")
        print("3. ❌ Sair")
        
        while True:
            escolha = input("\nDigite sua escolha (1-3): ").strip()
            
            if escolha == "1":
                main()
                break
            elif escolha == "2":
                teste_analise()
                break
            elif escolha == "3":
                print("👋 Até logo!")
                break
            else:
                print("❌ Opção inválida. Digite 1, 2 ou 3.")