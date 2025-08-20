#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da validação de email no frontend
Testa a nova funcionalidade de verificação de email ao sair do campo
"""

import requests
import json

def test_check_email_auth_type():
    """Testa a rota /check-email-auth-type"""
    base_url = "http://localhost:5000"
    
    # Teste 1: Email não existente
    print("\n=== Teste 1: Email não existente ===")
    response = requests.post(
        f"{base_url}/check-email-auth-type",
        json={"email": "teste.nao.existe@gmail.com"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")
    
    # Teste 2: Email com Google (se existir)
    print("\n=== Teste 2: Email com Google ===")
    response = requests.post(
        f"{base_url}/check-email-auth-type",
        json={"email": "paulotestario@gmail.com"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")
    
    # Teste 3: Email vazio
    print("\n=== Teste 3: Email vazio ===")
    response = requests.post(
        f"{base_url}/check-email-auth-type",
        json={"email": ""},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")
    
    # Teste 4: Email com espaços
    print("\n=== Teste 4: Email com espaços ===")
    response = requests.post(
        f"{base_url}/check-email-auth-type",
        json={"email": "  paulotestario@gmail.com  "},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")

if __name__ == "__main__":
    print("🧪 Testando validação de email no frontend...")
    try:
        test_check_email_auth_type()
        print("\n✅ Testes concluídos!")
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")