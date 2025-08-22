from database import Database
from datetime import datetime, timedelta
import calendar

class DynamicPricingSystem:
    def __init__(self):
        self.db = Database()
    
    def calculate_regional_demand(self, municipio_id: int, start_date: str, end_date: str) -> dict:
        """
        Calcula a demanda regional para um período específico
        """
        try:
            # Buscar todas as reservas no período
            bookings_result = self.db.supabase.table('listing_bookings').select(
                'listing_id, checkin_date, checkout_date, price_per_night'
            ).execute()
            
            # Buscar anúncios da região
            listings_result = self.db.supabase.table('user_listings').select(
                'id, price_per_night'
            ).eq('municipio_id', municipio_id).eq('is_active', True).execute()
            
            if not listings_result.data:
                return {'demand_score': 0, 'reason': 'Nenhum anúncio ativo na região'}
            
            total_listings = len(listings_result.data)
            listing_ids = [l['id'] for l in listings_result.data]
            
            # Calcular métricas por data
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            total_demand_score = 0
            days_analyzed = 0
            
            current_date = start
            while current_date <= end:
                date_str = current_date.strftime('%Y-%m-%d')
                
                # Contar reservas para esta data
                booked_count = 0
                total_price = 0
                
                for booking in bookings_result.data:
                    if booking['listing_id'] in listing_ids:
                        checkin = datetime.strptime(booking['checkin_date'], '%Y-%m-%d')
                        checkout = datetime.strptime(booking['checkout_date'], '%Y-%m-%d')
                        
                        if checkin <= current_date < checkout:
                            booked_count += 1
                            total_price += booking.get('price_per_night', 0)
                
                # Calcular taxa de ocupação
                occupancy_rate = (booked_count / total_listings) * 100 if total_listings > 0 else 0
                
                # Determinar tipo de período
                period_type = self._get_period_type(current_date)
                
                # Calcular score de demanda (0-100)
                demand_score = min(occupancy_rate * 1.2, 100)  # Multiplicador para amplificar demanda
                
                # Ajustar score baseado no tipo de período
                if period_type == 'weekend':
                    demand_score *= 1.3
                elif period_type == 'holiday':
                    demand_score *= 1.5
                elif period_type == 'high_season':
                    demand_score *= 1.4
                
                demand_score = min(demand_score, 100)
                
                # Salvar dados de demanda
                self._save_regional_demand(
                    municipio_id, date_str, period_type, 
                    total_listings, total_listings - booked_count, booked_count,
                    total_price / booked_count if booked_count > 0 else 0,
                    demand_score, occupancy_rate
                )
                
                total_demand_score += demand_score
                days_analyzed += 1
                current_date += timedelta(days=1)
            
            avg_demand_score = total_demand_score / days_analyzed if days_analyzed > 0 else 0
            
            return {
                'demand_score': round(avg_demand_score, 2),
                'total_listings': total_listings,
                'days_analyzed': days_analyzed,
                'reason': f'Análise de {days_analyzed} dias na região'
            }
            
        except Exception as e:
            print(f"❌ Erro ao calcular demanda regional: {e}")
            return {'demand_score': 0, 'reason': f'Erro: {str(e)}'}
    
    def _get_period_type(self, date: datetime) -> str:
        """
        Determina o tipo de período para uma data
        """
        # Verificar se é fim de semana
        if date.weekday() >= 5:  # Sábado = 5, Domingo = 6
            return 'weekend'
        
        # Verificar se é alta temporada (dezembro-março no RJ)
        if date.month in [12, 1, 2, 3]:
            return 'high_season'
        
        # Verificar feriados (simplificado)
        holidays = [
            (1, 1),   # Ano Novo
            (4, 21),  # Tiradentes
            (9, 7),   # Independência
            (10, 12), # Nossa Senhora Aparecida
            (11, 2),  # Finados
            (11, 15), # Proclamação da República
            (12, 25), # Natal
        ]
        
        if (date.month, date.day) in holidays:
            return 'holiday'
        
        return 'weekday'
    
    def _save_regional_demand(self, municipio_id: int, date: str, period_type: str,
                             total_listings: int, available_listings: int, booked_listings: int,
                             avg_price: float, demand_score: float, occupancy_rate: float):
        """
        Salva dados de demanda regional
        """
        try:
            data = {
                'municipio_id': municipio_id,
                'date': date,
                'period_type': period_type,
                'total_listings': total_listings,
                'available_listings': available_listings,
                'booked_listings': booked_listings,
                'avg_price': avg_price,
                'demand_score': demand_score,
                'occupancy_rate': occupancy_rate,
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.db.supabase.table('regional_demand').upsert(
                data, on_conflict='municipio_id,date,period_type'
            ).execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Erro ao salvar demanda regional: {e}")
            return False
    
    def calculate_dynamic_price(self, listing_id: int, date: str, base_price: float) -> dict:
        """
        Calcula preço dinâmico baseado na demanda regional
        """
        try:
            # Buscar informações do anúncio
            listing_result = self.db.supabase.table('user_listings').select(
                'municipio_id, property_type, is_beachfront'
            ).eq('id', listing_id).execute()
            
            if not listing_result.data:
                return {'dynamic_price': base_price, 'multiplier': 1.0, 'reason': 'Anúncio não encontrado'}
            
            listing = listing_result.data[0]
            municipio_id = listing['municipio_id']
            
            if not municipio_id:
                return {'dynamic_price': base_price, 'multiplier': 1.0, 'reason': 'Município não definido'}
            
            # Buscar demanda regional para a data
            demand_result = self.db.supabase.table('regional_demand').select(
                'demand_score, period_type, occupancy_rate'
            ).eq('municipio_id', municipio_id).eq('date', date).execute()
            
            if not demand_result.data:
                # Se não há dados de demanda, calcular para o período
                demand_data = self.calculate_regional_demand(municipio_id, date, date)
                demand_score = demand_data.get('demand_score', 0)
                period_type = self._get_period_type(datetime.strptime(date, '%Y-%m-%d'))
            else:
                demand_info = demand_result.data[0]
                demand_score = demand_info['demand_score']
                period_type = demand_info['period_type']
            
            # Calcular multiplicador baseado na demanda
            multiplier = 1.0
            reason_parts = []
            
            # Ajuste baseado no score de demanda
            if demand_score >= 80:
                multiplier += 0.4  # +40% para demanda muito alta
                reason_parts.append('demanda muito alta')
            elif demand_score >= 60:
                multiplier += 0.25  # +25% para demanda alta
                reason_parts.append('demanda alta')
            elif demand_score >= 40:
                multiplier += 0.1   # +10% para demanda média
                reason_parts.append('demanda média')
            elif demand_score < 20:
                multiplier -= 0.1   # -10% para demanda baixa
                reason_parts.append('demanda baixa')
            
            # Ajuste baseado no tipo de período
            if period_type == 'holiday':
                multiplier += 0.2
                reason_parts.append('feriado')
            elif period_type == 'weekend':
                multiplier += 0.15
                reason_parts.append('fim de semana')
            elif period_type == 'high_season':
                multiplier += 0.1
                reason_parts.append('alta temporada')
            
            # Ajuste para propriedades frente à praia
            if listing.get('is_beachfront'):
                multiplier += 0.1
                reason_parts.append('frente à praia')
            
            # Limitar multiplicador entre 0.7 e 2.0
            multiplier = max(0.7, min(2.0, multiplier))
            
            dynamic_price = round(base_price * multiplier, 2)
            
            # Salvar histórico
            self._save_dynamic_pricing_history(
                listing_id, date, base_price, dynamic_price, 
                demand_score, multiplier, ', '.join(reason_parts)
            )
            
            return {
                'dynamic_price': dynamic_price,
                'multiplier': round(multiplier, 2),
                'demand_score': demand_score,
                'reason': ', '.join(reason_parts) if reason_parts else 'preço base'
            }
            
        except Exception as e:
            print(f"❌ Erro ao calcular preço dinâmico: {e}")
            return {'dynamic_price': base_price, 'multiplier': 1.0, 'reason': f'Erro: {str(e)}'}
    
    def _save_dynamic_pricing_history(self, listing_id: int, date: str, original_price: float,
                                     dynamic_price: float, demand_score: float, 
                                     multiplier: float, reason: str):
        """
        Salva histórico de precificação dinâmica
        """
        try:
            data = {
                'listing_id': listing_id,
                'date': date,
                'original_price': original_price,
                'dynamic_price': dynamic_price,
                'demand_score': demand_score,
                'price_multiplier': multiplier,
                'reason': reason,
                'applied_at': datetime.now().isoformat()
            }
            
            result = self.db.supabase.table('dynamic_pricing_history').upsert(
                data, on_conflict='listing_id,date'
            ).execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Erro ao salvar histórico de preços: {e}")
            return False
    
    def apply_dynamic_pricing_to_listing(self, listing_id: int, start_date: str, end_date: str):
        """
        Aplica precificação dinâmica a um anúncio para um período
        """
        try:
            # Buscar preço base do anúncio
            listing_result = self.db.supabase.table('user_listings').select(
                'price_per_night, title'
            ).eq('id', listing_id).execute()
            
            if not listing_result.data:
                print(f"❌ Anúncio {listing_id} não encontrado")
                return False
            
            listing = listing_result.data[0]
            base_price = listing.get('price_per_night', 0)
            title = listing.get('title', 'Sem título')
            
            if base_price <= 0:
                print(f"❌ Preço base inválido para o anúncio {listing_id}")
                return False
            
            print(f"\n🏠 Aplicando preços dinâmicos para: {title}")
            print(f"💰 Preço base: R$ {base_price:.2f}")
            print(f"📅 Período: {start_date} a {end_date}")
            print("-" * 50)
            
            # Processar cada data no período
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            current_date = start
            while current_date <= end:
                date_str = current_date.strftime('%Y-%m-%d')
                
                # Calcular preço dinâmico
                pricing_result = self.calculate_dynamic_price(listing_id, date_str, base_price)
                
                # Atualizar disponibilidade com novo preço
                self.db.save_listing_availability(
                    listing_id=listing_id,
                    user_id=1,  # Assumindo user_id 1 para teste
                    date=date_str,
                    is_available=True,
                    price_per_night=pricing_result['dynamic_price']
                )
                
                # Mostrar resultado
                day_name = current_date.strftime('%A')
                print(f"📅 {date_str} ({day_name}):")
                print(f"   💰 Preço: R$ {base_price:.2f} → R$ {pricing_result['dynamic_price']:.2f}")
                print(f"   📊 Multiplicador: {pricing_result['multiplier']}x")
                print(f"   📈 Score demanda: {pricing_result['demand_score']:.1f}")
                print(f"   📝 Motivo: {pricing_result['reason']}")
                print()
                
                current_date += timedelta(days=1)
            
            print("✅ Precificação dinâmica aplicada com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao aplicar precificação dinâmica: {e}")
            return False

if __name__ == "__main__":
    # Demonstração do sistema
    pricing_system = DynamicPricingSystem()
    
    print("🚀 SISTEMA DE PREÇO FLUTUANTE - DEMONSTRAÇÃO")
    print("=" * 60)
    
    # Exemplo: aplicar preços dinâmicos para um anúncio
    # Assumindo que existe um anúncio com ID 1
    listing_id = 1
    start_date = "2024-12-20"  # Período de alta temporada
    end_date = "2024-12-27"    # Incluindo fim de semana e feriados
    
    pricing_system.apply_dynamic_pricing_to_listing(listing_id, start_date, end_date)