#!/usr/bin/env python3
"""
Script para recriar todas as tabelas do banco de dados HostLink
Este script irá:
1. Conectar ao Supabase
2. Executar o script SQL para recriar todas as tabelas
3. Popular a tabela de municípios com os dados do RJ
4. Testar as operações básicas
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def get_supabase_client() -> Client:
    """Conecta ao Supabase"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("❌ Erro: SUPABASE_URL e SUPABASE_KEY devem estar definidas no arquivo .env")
        sys.exit(1)
    
    return create_client(url, key)

def read_sql_file(filename: str) -> str:
    """Lê o conteúdo de um arquivo SQL"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo {filename} não encontrado")
        sys.exit(1)

def execute_sql_script(supabase: Client, sql_script: str):
    """Executa um script SQL no Supabase"""
    try:
        # Dividir o script em comandos individuais
        commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip()]
        
        for i, command in enumerate(commands):
            if command:
                print(f"Executando comando {i+1}/{len(commands)}...")
                result = supabase.rpc('exec_sql', {'sql': command}).execute()
                if result.data:
                    print(f"✅ Comando executado com sucesso")
        
        print("✅ Script SQL executado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao executar script SQL: {str(e)}")
        print("\n📝 Execute manualmente no editor SQL do Supabase:")
        print("https://supabase.com/dashboard/project/[SEU_PROJECT_ID]/sql")
        print("\nScript SQL:")
        print(sql_script)

def populate_municipios(supabase: Client):
    """Popula a tabela de municípios com dados do RJ"""
    try:
        # Verificar se já existem municípios
        result = supabase.table('municipios').select('count').execute()
        if result.data and len(result.data) > 0:
            print("ℹ️  Municípios já existem na base de dados")
            return
        
        # Ler e executar o script de municípios
        if os.path.exists('insert_municipios_rj.sql'):
            municipios_sql = read_sql_file('insert_municipios_rj.sql')
            print("📍 Populando tabela de municípios...")
            execute_sql_script(supabase, municipios_sql)
        else:
            print("⚠️  Arquivo insert_municipios_rj.sql não encontrado")
            
    except Exception as e:
        print(f"❌ Erro ao popular municípios: {str(e)}")

def test_database(supabase: Client):
    """Testa as operações básicas do banco"""
    try:
        print("\n🧪 Testando operações do banco de dados...")
        
        # Testar tabela de municípios
        municipios = supabase.table('municipios').select('*').limit(1).execute()
        print(f"✅ Municípios: {len(municipios.data)} registros encontrados")
        
        # Testar outras tabelas
        tables = ['users', 'user_listings', 'analyses', 'weather_data', 'competitors', 'pricing_history']
        for table in tables:
            result = supabase.table(table).select('count').execute()
            print(f"✅ Tabela {table}: OK")
        
        print("\n🎉 Todas as tabelas foram criadas e testadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro nos testes: {str(e)}")

def main():
    """Função principal"""
    print("🚀 Iniciando recriação do banco de dados HostLink...\n")
    
    # Conectar ao Supabase
    print("🔌 Conectando ao Supabase...")
    supabase = get_supabase_client()
    print("✅ Conectado com sucesso!\n")
    
    # Executar script de recriação
    print("📋 Executando script de recriação das tabelas...")
    sql_script = read_sql_file('recreate_tables.sql')
    execute_sql_script(supabase, sql_script)
    
    # Popular municípios
    print("\n📍 Populando dados dos municípios...")
    populate_municipios(supabase)
    
    # Testar banco
    test_database(supabase)
    
    print("\n✨ Processo concluído! O banco de dados está pronto para uso.")
    print("\n📝 Próximos passos:")
    print("1. Execute 'python web_app.py' para iniciar o servidor")
    print("2. Acesse http://localhost:5000 para testar a aplicação")
    print("3. Faça login com Google para testar o sistema de usuários")

if __name__ == '__main__':
    main()