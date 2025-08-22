from dynamic_pricing_system import DynamicPricingSystem
from database import Database
from datetime import datetime, timedelta

def test_dynamic_pricing_system():
    """Testa o sistema de preço dinâmico completo"""
    
    print("🧪 TESTE DO SISTEMA DE PREÇO DINÂMICO")
    print("=" * 50)
    
    db = Database()
    pricing_system = DynamicPricingSystem()
    
    # 1. Verificar se existem anúncios
    listings_result = db.supabase.table('user_listings').select(
        'id, title, price_per_night, municipio_id'
    ).eq('is_active', True).limit(3).execute()
    
    if not listings_result.data:
        print("❌ Nenhum anúncio encontrado para teste")
        return
    
    print(f"✅ Encontrados {len(listings_result.data)} anúncios para teste\n")
    
    # 2. Testar cada anúncio
    for listing in listings_result.data:
        listing_id = listing['id']
        title = listing['title']
        base_price = listing.get('price_per_night', 100)
        municipio_id = listing.get('municipio_id')
        
        print(f"🏠 Testando anúncio: {title}")
        print(f"💰 Preço base: R$ {base_price:.2f}")
        print(f"🏙️ Município ID: {municipio_id}")
        
        # Testar diferentes cenários de data
        test_dates = [
            ("2024-12-23", "Segunda-feira (véspera de Natal)"),
            ("2024-12-25", "Quarta-feira (Natal)"),
            ("2024-12-28", "Sábado (fim de semana)"),
            ("2024-12-31", "Terça-feira (véspera de Ano Novo)"),
            ("2025-01-15", "Quarta-feira (dia comum)"),
        ]
        
        for date_str, description in test_dates:
            result = pricing_system.calculate_dynamic_price(
                listing_id, date_str, base_price
            )
            
            print(f"  📅 {date_str} ({description}):")
            print(f"     💰 R$ {base_price:.2f} → R$ {result['dynamic_price']:.2f}")
            print(f"     📊 Multiplicador: {result['multiplier']}x")
            print(f"     📈 Score: {result['demand_score']:.1f}")
            print(f"     📝 Motivo: {result['reason']}")
        
        print("-" * 40)
    
    # 3. Testar aplicação de preços para um período
    if listings_result.data:
        first_listing = listings_result.data[0]
        listing_id = first_listing['id']
        
        print(f"\n🎯 Aplicando preços dinâmicos para período completo")
        print(f"🏠 Anúncio: {first_listing['title']}")
        
        success = pricing_system.apply_dynamic_pricing_to_listing(
            listing_id, "2024-12-20", "2024-12-27"
        )
        
        if success:
            print("\n✅ Teste concluído com sucesso!")
            
            # Mostrar histórico salvo
            history_result = db.supabase.table('dynamic_pricing_history').select(
                '*'
            ).eq('listing_id', listing_id).order('date').execute()
            
            if history_result.data:
                print("\n📊 HISTÓRICO DE PREÇOS SALVOS:")
                for record in history_result.data[-5:]:  # Últimos 5 registros
                    print(f"  📅 {record['date']}: R$ {record['original_price']:.2f} → R$ {record['dynamic_price']:.2f}")
                    print(f"     📝 {record['reason']}")
        else:
            print("❌ Erro no teste")

if __name__ == "__main__":
    test_dynamic_pricing_system()