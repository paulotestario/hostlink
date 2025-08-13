# 🚀 Deploy HostLink em Produção

Guia completo para executar o HostLink em ambiente de produção.

## 📋 Pré-requisitos

### 1. Banco de Dados (Supabase)
- Conta no [Supabase](https://supabase.com)
- Projeto criado com as tabelas necessárias
- Execute os scripts SQL:
  ```sql
  -- 1. Criar tabelas básicas
  \i scripts_tabela_anuncios.sql
  
  -- 2. Adicionar colunas extras
  \i alter_diferenca_anuncios.sql
  
  -- 3. Inserir municípios do RJ
  \i insert_municipios_rj.sql
  ```

### 2. Google OAuth
- Projeto no [Google Cloud Console](https://console.cloud.google.com/)
- API Google+ habilitada
- Credenciais OAuth 2.0 configuradas
- URLs de redirecionamento autorizadas para produção

## 🌐 Opções de Deploy

### Opção 1: Vercel (Serverless) ⭐ Recomendado

#### Vantagens:
- Deploy automático via Git
- SSL gratuito
- CDN global
- Fácil configuração

#### Limitações:
- Monitoramento automático limitado
- Cold starts
- Timeout de 10s (plano gratuito)

#### Passos:

1. **Preparar repositório Git:**
   ```bash
   git init
   git add .
   git commit -m "Deploy HostLink para produção"
   git remote add origin https://github.com/seu-usuario/hostlink.git
   git push -u origin main
   ```

2. **Deploy no Vercel:**
   - Acesse [vercel.com](https://vercel.com)
   - Conecte seu repositório GitHub
   - Vercel detectará automaticamente o `vercel.json`

3. **Configurar variáveis de ambiente:**
   ```
   FLASK_SECRET_KEY=sua_chave_secreta_super_forte
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua_chave_anon_public
   GOOGLE_CLIENT_ID=seu_google_client_id
   GOOGLE_CLIENT_SECRET=seu_google_client_secret
   GOOGLE_REDIRECT_URI=https://seu-dominio.vercel.app/auth/callback
   ```

### Opção 2: Render.com (Servidor Persistente)

#### Vantagens:
- Servidor sempre ativo
- Monitoramento automático funciona
- Banco PostgreSQL gratuito
- SSL automático

#### Passos:

1. **Criar conta no [Render.com](https://render.com)**

2. **Criar Web Service:**
   - Conectar repositório GitHub
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python web_app.py`

3. **Configurar variáveis de ambiente** (mesmo que Vercel)

### Opção 3: Railway.app

#### Vantagens:
- Deploy simples
- Banco PostgreSQL incluído
- Monitoramento automático

#### Passos:

1. **Criar conta no [Railway.app](https://railway.app)**
2. **Deploy from GitHub**
3. **Configurar variáveis de ambiente**

### Opção 4: PythonAnywhere

#### Vantagens:
- Especializado em Python
- Cron jobs gratuitos
- Fácil configuração

#### Passos:

1. **Criar conta no [PythonAnywhere](https://pythonanywhere.com)**
2. **Upload dos arquivos**
3. **Configurar Web App Flask**
4. **Configurar variáveis de ambiente no arquivo `.env`**

## ⚙️ Configuração de Produção

### 1. Arquivo `.env` para Produção

Crie um arquivo `.env` com:

```env
# Flask
FLASK_SECRET_KEY=sua_chave_secreta_muito_forte_aqui_min_32_chars
FLASK_ENV=production

# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave_anon_public_supabase

# Google OAuth
GOOGLE_CLIENT_ID=seu_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=seu_google_client_secret
GOOGLE_REDIRECT_URI=https://seu-dominio.com/auth/callback

# Email (Opcional)
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_app_gmail
EMAIL_RECIPIENT=destinatario@gmail.com
```

### 2. Configurações de Segurança

#### Gerar chave secreta forte:
```python
import secrets
print(secrets.token_hex(32))
```

#### URLs de redirecionamento OAuth:
- Desenvolvimento: `http://localhost:5000/auth/callback`
- Produção: `https://seu-dominio.com/auth/callback`

### 3. Configuração do Supabase

#### Políticas de Segurança (RLS):
```sql
-- Habilitar RLS
ALTER TABLE user_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Política para user_listings
CREATE POLICY "Users can view own listings" ON user_listings
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Política para analyses
CREATE POLICY "Users can view own analyses" ON analyses
    FOR ALL USING (auth.uid()::text = user_id::text);
```

## 🔄 Monitoramento Automático

### Para Vercel (Serverless):

#### Opção 1: GitHub Actions
Crie `.github/workflows/monitor.yml`:
```yaml
name: Monitor HostLink
on:
  schedule:
    - cron: '*/5 * * * *'  # A cada 5 minutos
  workflow_dispatch:

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger monitoring
        run: |
          curl -X POST "https://seu-dominio.vercel.app/api/monitor" \
               -H "Authorization: Bearer ${{ secrets.MONITOR_TOKEN }}"
```

#### Opção 2: Cron-job.org
- Acesse [cron-job.org](https://cron-job.org)
- Configure URL: `https://seu-dominio.vercel.app/api/monitor`
- Intervalo: 5 minutos

### Para Render/Railway (Servidor Persistente):
O monitoramento automático funcionará normalmente.

## 🧪 Teste de Produção

### Script de Teste:
```bash
# Testar endpoints principais
curl https://seu-dominio.com/
curl https://seu-dominio.com/api/health
curl https://seu-dominio.com/perfil
```

### Verificar logs:
- **Vercel**: Dashboard → Functions → View Logs
- **Render**: Dashboard → Logs
- **Railway**: Dashboard → Deployments → Logs

## 🔧 Troubleshooting

### Problemas Comuns:

1. **Erro de conexão com Supabase:**
   - Verificar URL e chave
   - Verificar políticas RLS
   - Verificar se tabelas existem

2. **Erro OAuth Google:**
   - Verificar Client ID/Secret
   - Verificar URL de redirecionamento
   - Verificar se API está habilitada

3. **Timeout em análises:**
   - Otimizar consultas
   - Usar cache
   - Dividir em múltiplas requisições

4. **Cold starts (Vercel):**
   - Usar Vercel Pro para reduzir
   - Implementar warming requests
   - Considerar servidor persistente

## 📊 Monitoramento e Logs

### Métricas importantes:
- Tempo de resposta
- Taxa de erro
- Uso de memória
- Número de usuários ativos

### Ferramentas recomendadas:
- **Uptime**: UptimeRobot, Pingdom
- **Analytics**: Google Analytics, Plausible
- **Errors**: Sentry, Rollbar
- **Performance**: New Relic, DataDog

## 🚀 Próximos Passos

1. **Configurar domínio personalizado**
2. **Implementar cache Redis**
3. **Adicionar testes automatizados**
4. **Configurar CI/CD**
5. **Implementar backup automático**
6. **Adicionar monitoramento avançado**

---

**✅ Checklist de Deploy:**
- [ ] Banco de dados configurado
- [ ] Variáveis de ambiente definidas
- [ ] Google OAuth configurado
- [ ] SSL habilitado
- [ ] Monitoramento configurado
- [ ] Testes de produção executados
- [ ] Backup configurado
- [ ] Domínio personalizado (opcional)

**🎉 Seu HostLink está pronto para produção!**