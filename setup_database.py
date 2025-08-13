#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Configuração do Banco de Dados
Configura e testa a conexão com o Supabase
"""

import os
from database import get_database
from dotenv import load_dotenv

def main():
    print("🔧 Configurando banco de dados HostLink...\n")
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar se as credenciais estão configuradas
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or supabase_url == 'your_supabase_url_here':
        print("❌ SUPABASE_URL não configurada!")
        print("📝 Edite o arquivo .env e adicione sua URL do Supabase")
        print("💡 Exemplo: SUPABASE_URL=https://seu-projeto.supabase.co")
        return False
    
    if not supabase_key or supabase_key == 'your_supabase_anon_key_here':
        print("❌ SUPABASE_KEY não configurada!")
        print("📝 Edite o arquivo .env e adicione sua chave anônima do Supabase")
        print("💡 Encontre em: Projeto > Settings > API > anon public")
        return False
    
    print(f"🔗 URL do Supabase: {supabase_url}")
    print(f"🔑 Chave configurada: {supabase_key[:20]}...\n")
    
    # Tentar conectar
    print("🔌 Testando conexão...")
    db = get_database()
    
    if not db:
        print("❌ Falha ao inicializar banco de dados")
        return False
    
    # Testar conexão
    if db.test_connection():
        print("\n📋 SQL para criar tabelas:")
        print("=" * 50)
        print(db.create_tables())
        print("=" * 50)
        print("\n📝 Instruções:")
        print("1. Copie o SQL acima")
        print("2. Acesse seu projeto no Supabase")
        print("3. Vá em 'SQL Editor'")
        print("4. Cole e execute o SQL")
        print("5. Execute este script novamente para testar")
        
        # Testar se as tabelas existem
        try:
            result = db.supabase.table('analyses').select('count').execute()
            print("\n✅ Tabelas já existem e estão funcionando!")
            print("🚀 Banco de dados pronto para uso!")
            return True
        except Exception as e:
            print(f"\n⚠️ Tabelas ainda não criadas")
            print("📝 Execute o SQL acima no Supabase primeiro")
            print("\n🔗 Link direto para SQL Editor:")
            print(f"https://supabase.com/dashboard/project/{os.getenv('SUPABASE_URL', '').split('//')[1].split('.')[0]}/sql")
            return False
    else:
        print("❌ Falha na conexão com Supabase")
        print("🔍 Verifique suas credenciais no arquivo .env")
        return False

def test_database_operations():
    """Testa operações básicas do banco"""
    print("\n🧪 Testando operações do banco...")
    
    db = get_database()
    if not db:
        print("❌ Banco não disponível")
        return False
    
    try:
        # Teste de inserção
        test_analysis = {
            'checkin': '2025-08-08',
            'checkout': '2025-08-10',
            'adults': 2,
            'beachfront': True,
            'period_type': 'weekend',
            'is_weekend': True,
            'pricing_suggestion': {
                'suggested_price': 350.0,
                'price_multiplier': 1.3,
                'justification': 'Teste de integração',
                'discount_percentage': 0,
                'average_competitor_price': 300.0
            },
            'weather_data': [{
                'date': '2025-08-08',
                'rain_probability': 20,
                'weather_condition': 'Ensolarado',
                'description': 'Tempo bom para praia'
            }],
            'competitive_data': [{
                'title': 'Casa de Teste',
                'price': 300.0,
                'rating': 4.5,
                'reviews': 25,
                'distance': '500m da praia',
                'is_beachfront': True
            }]
        }
        
        # Salvar análise de teste
        analysis_id = db.save_analysis(test_analysis)
        if analysis_id:
            print(f"✅ Análise de teste salva com ID: {analysis_id}")
            
            # Recuperar análise
            latest = db.get_latest_analysis()
            if latest:
                print("✅ Recuperação de dados funcionando")
                
                # Histórico
                history = db.get_analysis_history(5)
                print(f"✅ Histórico recuperado: {len(history)} registros")
                
                print("\n🎉 Todos os testes passaram!")
                print("💾 Banco de dados totalmente funcional!")
                return True
            else:
                print("❌ Erro ao recuperar dados")
                return False
        else:
            print("❌ Erro ao salvar análise de teste")
            return False
            
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        return False

if __name__ == '__main__':
    success = main()
    
    if success:
        # Se a conexão funcionou, testar operações
        test_success = test_database_operations()
        
        if test_success:
            print("\n🚀 Configuração completa!")
            print("📊 O HostLink agora está integrado com Supabase")
            print("💡 Execute 'py web_app.py' para iniciar com persistência")
        else:
            print("\n⚠️ Conexão OK, mas operações falharam")
            print("🔍 Verifique se as tabelas foram criadas corretamente")
    else:
        print("\n❌ Configuração incompleta")
        print("📝 Siga as instruções acima para configurar o Supabase")