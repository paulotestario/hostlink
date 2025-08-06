#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Consulta Personalizada
Permite ao usuário inserir datas específicas para análise
"""

from airbnb_scraper import AirbnbClimateScraper
from datetime import datetime
import sys

def validar_data(data_str):
    """
    Valida se a data está no formato correto YYYY-MM-DD
    """
    try:
        datetime.strptime(data_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def consulta_interativa():
    """
    Função para consulta interativa com o usuário
    """
    print("🏖️ Consulta Personalizada - Hotel Mont Blanc Itacuruçá")
    print("="*55)
    
    # Solicitar dados do usuário
    while True:
        checkin = input("\n📅 Data de check-in (YYYY-MM-DD): ").strip()
        if validar_data(checkin):
            break
        print("❌ Formato inválido! Use YYYY-MM-DD (ex: 2025-08-08)")
    
    while True:
        checkout = input("📅 Data de check-out (YYYY-MM-DD): ").strip()
        if validar_data(checkout):
            # Verificar se checkout é depois de checkin
            checkin_dt = datetime.strptime(checkin, '%Y-%m-%d')
            checkout_dt = datetime.strptime(checkout, '%Y-%m-%d')
            if checkout_dt > checkin_dt:
                break
            else:
                print("❌ Data de check-out deve ser posterior ao check-in!")
        else:
            print("❌ Formato inválido! Use YYYY-MM-DD (ex: 2025-08-10)")
    
    while True:
        try:
            adultos = int(input("👥 Número de adultos (padrão 2): ") or "2")
            if adultos > 0:
                break
            else:
                print("❌ Número de adultos deve ser maior que 0!")
        except ValueError:
            print("❌ Digite um número válido!")
    
    print("\n🔄 Iniciando análise...")
    print("="*55)
    
    # Executar análise
    scraper = AirbnbClimateScraper()
    results = scraper.run_analysis(checkin, checkout, adultos)
    
    # Resumo final
    print("\n" + "="*55)
    print("📊 RESUMO DA ANÁLISE")
    print("="*55)
    
    if results:
        for i, result in enumerate(results, 1):
            listing = result['listing']
            pricing = result['pricing_suggestion']
            
            print(f"\n🏨 Opção {i}: {listing['name']}")
            print(f"💰 Preço original: R$ {listing['price_per_night']:.2f}/noite")
            print(f"💡 Preço sugerido: R$ {pricing['suggested_price']:.2f}/noite")
            
            # Calcular total da estadia
            nights = (datetime.strptime(checkout, '%Y-%m-%d') - datetime.strptime(checkin, '%Y-%m-%d')).days
            total_original = listing['price_per_night'] * nights
            total_sugerido = pricing['suggested_price'] * nights
            
            print(f"📊 Total da estadia ({nights} noites):")
            print(f"   • Preço original: R$ {total_original:.2f}")
            print(f"   • Preço sugerido: R$ {total_sugerido:.2f}")
            print(f"   • Diferença: R$ {total_sugerido - total_original:.2f}")
            
            print(f"🌧️ Clima: {pricing['avg_rain_probability']:.1f}% chance de chuva")
            print(f"📈 Justificativa: {pricing['weather_factor']}")
            
            if pricing['is_weekend']:
                print("🎉 Final de semana - Premium aplicado")
    
    print("\n✅ Análise concluída com sucesso!")
    return results

def consulta_rapida_args():
    """
    Função para consulta via argumentos da linha de comando
    Uso: python consulta_personalizada.py YYYY-MM-DD YYYY-MM-DD [adultos]
    """
    if len(sys.argv) < 3:
        print("❌ Uso: python consulta_personalizada.py checkin checkout [adultos]")
        print("   Exemplo: python consulta_personalizada.py 2025-08-08 2025-08-10 2")
        return None
    
    checkin = sys.argv[1]
    checkout = sys.argv[2]
    adultos = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    
    # Validar datas
    if not validar_data(checkin) or not validar_data(checkout):
        print("❌ Formato de data inválido! Use YYYY-MM-DD")
        return None
    
    # Verificar se checkout é depois de checkin
    checkin_dt = datetime.strptime(checkin, '%Y-%m-%d')
    checkout_dt = datetime.strptime(checkout, '%Y-%m-%d')
    if checkout_dt <= checkin_dt:
        print("❌ Data de check-out deve ser posterior ao check-in!")
        return None
    
    print(f"🏖️ Análise Rápida - {checkin} a {checkout} ({adultos} adultos)")
    print("="*60)
    
    scraper = AirbnbClimateScraper()
    return scraper.run_analysis(checkin, checkout, adultos)

def main():
    """
    Função principal - decide entre modo interativo ou argumentos
    """
    if len(sys.argv) > 1:
        # Modo argumentos
        consulta_rapida_args()
    else:
        # Modo interativo
        try:
            consulta_interativa()
        except KeyboardInterrupt:
            print("\n\n❌ Operação cancelada pelo usuário")
        except Exception as e:
            print(f"\n\n❌ Erro durante a execução: {e}")
            print("💡 Verifique sua conexão com a internet e tente novamente")

if __name__ == "__main__":
    main()