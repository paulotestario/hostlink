#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de uso do AirbnbClimateScraper
Script para consultar preços do Hotel Mont Blanc em Itacuruçá e verificar o clima
"""

from airbnb_scraper import AirbnbClimateScraper
from datetime import datetime, timedelta

def main():
    print("🏖️ Sistema de Análise de Preços - Hotel Mont Blanc Itacuruçá")
    print("="*60)
    
    # Criar instância do scraper
    scraper = AirbnbClimateScraper()
    
    # Opção 1: Usar datas específicas (exemplo do usuário)
    print("\n📋 Opção 1: Análise para datas específicas")
    checkin_especifico = "2025-08-08"
    checkout_especifico = "2025-08-10"
    
    print(f"Analisando: {checkin_especifico} a {checkout_especifico}")
    results1 = scraper.run_analysis(checkin_especifico, checkout_especifico, adults=2)
    
    print("\n" + "="*60)
    
    # Opção 2: Próximo final de semana
    print("\n📋 Opção 2: Análise para o próximo final de semana")
    
    today = datetime.now()
    
    # Calcular próxima sexta-feira
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0 and today.weekday() >= 4:  # Se hoje é sexta, sábado ou domingo
        days_until_friday = 7  # Próxima sexta
    elif days_until_friday == 0:  # Se hoje é antes de sexta
        days_until_friday = 4 - today.weekday()
    
    next_friday = today + timedelta(days=days_until_friday)
    next_sunday = next_friday + timedelta(days=2)
    
    checkin_weekend = next_friday.strftime('%Y-%m-%d')
    checkout_weekend = next_sunday.strftime('%Y-%m-%d')
    
    print(f"Analisando: {checkin_weekend} a {checkout_weekend}")
    results2 = scraper.run_analysis(checkin_weekend, checkout_weekend, adults=2)
    
    print("\n" + "="*60)
    print("\n✅ Análise concluída!")
    print("\n💡 Dicas de uso:")
    print("   • Preços mais altos em finais de semana")
    print("   • Descontos aplicados em dias com alta probabilidade de chuva")
    print("   • Preços premium em dias ensolarados")
    print("   • Consulte sempre a previsão do tempo antes de definir preços")
    
    return results1, results2

def consulta_rapida(checkin, checkout, adultos=2):
    """
    Função para consulta rápida de preços
    
    Args:
        checkin (str): Data de check-in no formato 'YYYY-MM-DD'
        checkout (str): Data de check-out no formato 'YYYY-MM-DD'
        adultos (int): Número de adultos
    
    Returns:
        list: Resultados da análise
    """
    scraper = AirbnbClimateScraper()
    return scraper.run_analysis(checkin, checkout, adultos)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro durante a execução: {e}")
        print("\n💡 Verifique sua conexão com a internet e tente novamente")