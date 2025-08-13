#!/usr/bin/env python3
"""
Script automatizado para deploy do HostLink em produção
"""

import os
import sys
import subprocess
import secrets
from pathlib import Path

def print_header(title):
    """Imprime cabeçalho formatado"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    """Imprime passo formatado"""
    print(f"\n📋 Passo {step}: {description}")
    print("-" * 50)

def check_requirements():
    """Verifica se os requisitos estão instalados"""
    print_step(1, "Verificando requisitos")
    
    # Verificar se git está instalado
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        print("✅ Git instalado")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git não encontrado. Instale o Git primeiro.")
        return False
    
    # Verificar se requirements.txt existe
    if Path("requirements.txt").exists():
        print("✅ requirements.txt encontrado")
    else:
        print("❌ requirements.txt não encontrado")
        return False
    
    # Verificar se vercel.json existe
    if Path("vercel.json").exists():
        print("✅ vercel.json encontrado")
    else:
        print("❌ vercel.json não encontrado")
        return False
    
    return True

def generate_env_template():
    """Gera template do arquivo .env para produção"""
    print_step(2, "Gerando template .env para produção")
    
    # Gerar chave secreta forte
    secret_key = secrets.token_hex(32)
    
    env_template = f"""# HostLink - Configuração de Produção
# Gerado automaticamente em {os.path.basename(__file__)}

# Flask
FLASK_SECRET_KEY={secret_key}
FLASK_ENV=production

# Supabase - CONFIGURE ESTES VALORES
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_KEY=SUA_CHAVE_ANON_PUBLIC_AQUI

# Google OAuth - CONFIGURE ESTES VALORES
GOOGLE_CLIENT_ID=SEU_GOOGLE_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=SEU_GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI=https://SEU-DOMINIO.com/auth/callback

# Email (Opcional)
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_app_gmail
EMAIL_RECIPIENT=destinatario@gmail.com
"""
    
    with open(".env.production", "w", encoding="utf-8") as f:
        f.write(env_template)
    
    print("✅ Arquivo .env.production criado")
    print("⚠️  IMPORTANTE: Edite o arquivo .env.production com suas credenciais reais")
    
    return secret_key

def setup_git_repo():
    """Configura repositório Git se necessário"""
    print_step(3, "Configurando repositório Git")
    
    # Verificar se já é um repositório Git
    if Path(".git").exists():
        print("✅ Repositório Git já existe")
        return True
    
    try:
        # Inicializar repositório
        subprocess.run(["git", "init"], check=True)
        print("✅ Repositório Git inicializado")
        
        # Adicionar arquivos
        subprocess.run(["git", "add", "."], check=True)
        print("✅ Arquivos adicionados ao Git")
        
        # Commit inicial
        subprocess.run(["git", "commit", "-m", "Initial commit - HostLink ready for production"], check=True)
        print("✅ Commit inicial criado")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao configurar Git: {e}")
        return False

def create_deployment_scripts():
    """Cria scripts de deployment para diferentes plataformas"""
    print_step(4, "Criando scripts de deployment")
    
    # Script para Vercel
    vercel_script = """#!/bin/bash
# Deploy para Vercel

echo "🚀 Fazendo deploy para Vercel..."

# Instalar Vercel CLI se necessário
if ! command -v vercel &> /dev/null; then
    echo "📦 Instalando Vercel CLI..."
    npm install -g vercel
fi

# Login (se necessário)
echo "🔐 Faça login no Vercel se solicitado:"
vercel login

# Deploy
echo "🚀 Iniciando deploy..."
vercel --prod

echo "✅ Deploy concluído!"
echo "📋 Não esqueça de configurar as variáveis de ambiente no dashboard do Vercel"
"""
    
    with open("deploy_vercel.sh", "w", encoding="utf-8") as f:
        f.write(vercel_script)
    
    # Script para Render
    render_script = """#!/bin/bash
# Deploy para Render.com

echo "🚀 Preparando deploy para Render.com..."

# Verificar se o repositório tem remote
if ! git remote get-url origin &> /dev/null; then
    echo "❌ Configure o remote origin do Git primeiro:"
    echo "   git remote add origin https://github.com/seu-usuario/hostlink.git"
    exit 1
fi

# Push para GitHub
echo "📤 Enviando código para GitHub..."
git push origin main

echo "✅ Código enviado!"
echo "📋 Agora:"
echo "   1. Acesse https://render.com"
echo "   2. Conecte seu repositório GitHub"
echo "   3. Configure as variáveis de ambiente"
echo "   4. Faça o deploy"
"""
    
    with open("deploy_render.sh", "w", encoding="utf-8") as f:
        f.write(render_script)
    
    print("✅ Scripts de deployment criados:")
    print("   - deploy_vercel.sh")
    print("   - deploy_render.sh")

def create_health_check():
    """Cria endpoint de health check para monitoramento"""
    print_step(5, "Criando health check")
    
    # Verificar se web_app.py existe
    if not Path("web_app.py").exists():
        print("❌ web_app.py não encontrado")
        return False
    
    # Ler conteúdo atual
    with open("web_app.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verificar se health check já existe
    if "/health" in content:
        print("✅ Health check já existe")
        return True
    
    # Adicionar health check
    health_check_code = '''

@app.route('/health')
def health_check():
    """Endpoint de health check para monitoramento"""
    try:
        # Verificar conexão com banco
        db = get_database()
        if db:
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected',
                'version': '1.0.0'
            }), 200
        else:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'disconnected',
                'error': 'Database connection failed'
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 503

@app.route('/api/monitor')
def api_monitor():
    """Endpoint para monitoramento automático"""
    try:
        # Executar análise automática se configurado
        # (implementar lógica de monitoramento aqui)
        return jsonify({
            'status': 'monitoring_executed',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'monitoring_failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
'''
    
    # Adicionar imports necessários no topo
    if "from datetime import datetime" not in content:
        content = content.replace(
            "from flask import Flask",
            "from flask import Flask, jsonify\nfrom datetime import datetime"
        )
    
    # Adicionar health check antes da linha if __name__ == '__main__':
    if "if __name__ == '__main__':" in content:
        content = content.replace(
            "if __name__ == '__main__':",
            health_check_code + "\n\nif __name__ == '__main__':"
        )
    else:
        content += health_check_code
    
    # Salvar arquivo atualizado
    with open("web_app.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Health check adicionado ao web_app.py")
    return True

def show_next_steps(secret_key):
    """Mostra próximos passos para o usuário"""
    print_header("Próximos Passos")
    
    print("\n📋 Para completar o deploy:")
    print("\n1. 🔧 CONFIGURAR CREDENCIAIS:")
    print("   - Edite o arquivo .env.production")
    print("   - Configure Supabase URL e Key")
    print("   - Configure Google OAuth Client ID e Secret")
    print("   - Atualize GOOGLE_REDIRECT_URI com seu domínio")
    
    print("\n2. 🗄️ CONFIGURAR BANCO DE DADOS:")
    print("   - Execute os scripts SQL no Supabase:")
    print("     • scripts_tabela_anuncios.sql")
    print("     • alter_diferenca_anuncios.sql")
    print("     • insert_municipios_rj.sql")
    
    print("\n3. 🚀 ESCOLHER PLATAFORMA DE DEPLOY:")
    print("   \n   OPÇÃO A - Vercel (Serverless):")
    print("   - Execute: bash deploy_vercel.sh")
    print("   - Configure variáveis de ambiente no dashboard")
    print("   - Limitação: monitoramento automático limitado")
    
    print("   \n   OPÇÃO B - Render.com (Servidor):")
    print("   - Configure remote Git: git remote add origin https://github.com/seu-usuario/hostlink.git")
    print("   - Execute: bash deploy_render.sh")
    print("   - Vantagem: monitoramento automático funciona")
    
    print("   \n   OPÇÃO C - Railway.app:")
    print("   - Acesse railway.app")
    print("   - Deploy from GitHub")
    print("   - Configure variáveis de ambiente")
    
    print("\n4. 🔐 CONFIGURAR GOOGLE OAUTH:")
    print("   - Acesse Google Cloud Console")
    print("   - Adicione URL de redirecionamento: https://seu-dominio.com/auth/callback")
    
    print("\n5. 📊 CONFIGURAR MONITORAMENTO:")
    print("   - Health check disponível em: /health")
    print("   - Monitoramento em: /api/monitor")
    print("   - Configure cron job externo se usar Vercel")
    
    print(f"\n🔑 Sua chave secreta Flask: {secret_key}")
    print("   (já incluída no .env.production)")
    
    print("\n📖 Documentação completa: DEPLOY_PRODUCAO.md")
    
    print("\n🎉 Seu HostLink está pronto para produção!")

def main():
    """Função principal"""
    print_header("HostLink - Deploy para Produção")
    
    # Verificar se estamos no diretório correto
    if not Path("web_app.py").exists():
        print("❌ Execute este script no diretório raiz do HostLink")
        sys.exit(1)
    
    # Executar passos
    if not check_requirements():
        print("\n❌ Requisitos não atendidos. Corrija os problemas acima.")
        sys.exit(1)
    
    secret_key = generate_env_template()
    
    if not setup_git_repo():
        print("\n⚠️ Problemas com Git, mas continuando...")
    
    create_deployment_scripts()
    
    if not create_health_check():
        print("\n⚠️ Problemas ao criar health check, mas continuando...")
    
    show_next_steps(secret_key)

if __name__ == "__main__":
    main()