#!/usr/bin/env python3
"""
Script de teste para verificar se o salvamento de anúncios está funcionando
"""

import requests
import json

def test_save_listing():
    """Testa o salvamento de um anúncio via API"""
    
    # URL da API
    url = "http://localhost:5000/perfil/listing"
    
    # Dados de teste
    test_data = {
        "title": "Teste - Casa na Praia",
        "url": "https://www.airbnb.com.br/rooms/12345678",
        "platform": "airbnb",
        "property_type": "Casa inteira",
        "max_guests": 4,
        "bedrooms": 2,
        "bathrooms": 1
    }
    
    print(f"🧪 Testando salvamento de anúncio...")
    print(f"📝 Dados: {json.dumps(test_data, indent=2)}")
    
    try:
        # Fazer requisição POST
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Resposta: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Anúncio salvo com sucesso! ID: {result.get('listing_id')}")
            else:
                print(f"❌ Erro ao salvar: {result.get('error')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    test_save_listing()