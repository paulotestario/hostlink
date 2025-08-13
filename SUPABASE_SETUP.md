# 🗄️ Configuração do Supabase - HostLink

Guia completo para integrar o HostLink com o banco de dados Supabase.

## 📋 Pré-requisitos

- Conta no [Supabase](https://supabase.com/)
- Python 3.7+ instalado
- Projeto HostLink configurado

## 🚀 Configuração Rápida

### 1. Criar Projeto no Supabase

1. Acesse [supabase.com](https://supabase.com/)
2. Faça login ou crie uma conta
3. Clique em "New Project"
4. Escolha sua organização
5. Configure:
   - **Name**: `hostlink-db` (ou nome de sua preferência)
   - **Database Password**: Crie uma senha forte
   - **Region**: Escolha a região mais próxima
6. Clique em "Create new project"

### 2. Obter Credenciais

Após criar o projeto:

1. Vá para **Settings** → **API**
2. Copie:
   - **URL**: `https://seu-projeto.supabase.co`
   - **anon public**: Chave pública para acesso

### 3. Configurar Variáveis de Ambiente

Edite o arquivo `.env` na raiz do projeto:

```env
# Supabase Configuration
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave_anon_public_aqui

# Flask Configuration
FLASK_SECRET_KEY=sua_chave_secreta_flask

# Email Configuration (Opcional)
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_app
EMAIL_RECIPIENT=destinatario@gmail.com
```

### 4. Executar Configuração

```bash
# Instalar dependências (se ainda não instaladas)
py -m pip install supabase python-dotenv

# Executar script de configuração
py setup_database.py
```

### 5. Criar Tabelas no Supabase

O script `setup_database.py` irá gerar o SQL necessário. Copie e execute no **SQL Editor** do Supabase:

1. No painel do Supabase, vá para **SQL Editor**
2. Cole o SQL gerado pelo script
3. Clique em **Run** para executar

## 📊 Estrutura das Tabelas

### `analyses`
Armazena todas as análises realizadas:
- `id`: Identificador único
- `checkin/checkout`: Datas da reserva
- `adults`: Número de adultos
- `beachfront`: Se é frente para o mar
- `period_type`: Tipo do período (weekend, holiday, etc.)
- `pricing_suggestion`: Dados de precificação (JSON)
- `weather_data`: Dados meteorológicos (JSON)
- `competitive_data`: Dados da concorrência (JSON)
- `created_at`: Data de criação

### `pricing_history`
Histórico de preços sugeridos:
- `id`: Identificador único
- `checkin`: Data do check-in
- `suggested_price`: Preço sugerido
- `competitor_avg_price`: Preço médio da concorrência
- `price_multiplier`: Multiplicador aplicado
- `created_at`: Data de criação

## 🔧 Verificação da Instalação

### Teste de Conexão
```bash
py setup_database.py
```

### Teste Completo
O script irá:
1. ✅ Verificar credenciais
2. ✅ Testar conexão
3. ✅ Gerar SQL das tabelas
4. ✅ Testar operações CRUD
5. ✅ Confirmar funcionamento

## 🚀 Executar com Supabase

```bash
# Iniciar aplicação com banco de dados
py web_app.py
```

A aplicação agora irá:
- 💾 Salvar todas as análises no Supabase
- 📊 Carregar dados do banco na inicialização
- 🔄 Manter sincronização automática
- 📈 Preservar histórico completo

## 🔍 Monitoramento

### Logs da Aplicação
A aplicação mostra logs quando:
- ✅ Conecta com sucesso ao banco
- 💾 Salva nova análise
- 📊 Carrega dados do banco
- ⚠️ Encontra erros de conexão

### Painel do Supabase
1. **Table Editor**: Visualizar dados salvos
2. **SQL Editor**: Executar consultas personalizadas
3. **Logs**: Monitorar atividade do banco
4. **API**: Documentação automática da API

## 🛠️ Solução de Problemas

### Erro de Conexão
```
❌ Falha na conexão com Supabase
```
**Solução**: Verifique URL e chave no arquivo `.env`

### Tabelas Não Encontradas
```
⚠️ Tabelas ainda não criadas
```
**Solução**: Execute o SQL no SQL Editor do Supabase

### Erro de Permissão
```
❌ Erro ao salvar análise no banco
```
**Solução**: Verifique se a chave `anon` tem permissões adequadas

### Fallback para Memória
Se o banco não estiver disponível, a aplicação continua funcionando em memória.

## 📈 Benefícios da Integração

- **Persistência**: Dados não são perdidos ao reiniciar
- **Histórico**: Análises completas preservadas
- **Escalabilidade**: Banco em nuvem gerenciado
- **Backup**: Dados seguros e replicados
- **API**: Acesso aos dados via REST API
- **Real-time**: Atualizações em tempo real
- **Analytics**: Consultas SQL avançadas

## 🔐 Segurança

- ✅ Credenciais em arquivo `.env` (não commitado)
- ✅ Chaves de API com escopo limitado
- ✅ Conexão HTTPS criptografada
- ✅ Backup automático do Supabase
- ✅ Logs de auditoria

## 📞 Suporte

Se encontrar problemas:
1. Execute `py setup_database.py` para diagnóstico
2. Verifique logs da aplicação
3. Consulte documentação do [Supabase](https://supabase.com/docs)
4. Verifique configurações no painel do Supabase

---

**🎉 Parabéns!** Seu HostLink agora está integrado com Supabase e pronto para produção!