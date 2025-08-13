# 🔐 Configuração do Google OAuth - HostLink

Guia completo para configurar autenticação com Google OAuth no HostLink.

## 📋 Pré-requisitos

- Conta Google
- Projeto HostLink configurado
- Dependências instaladas (`flask-login`, `google-auth`, etc.)

## 🚀 Configuração Passo a Passo

### 1. Criar Projeto no Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Faça login com sua conta Google
3. Clique em "Selecionar projeto" → "Novo projeto"
4. Configure:
   - **Nome do projeto**: `hostlink-auth` (ou nome de sua preferência)
   - **Organização**: Deixe como está
5. Clique em "Criar"

### 2. Ativar APIs Necessárias

1. No painel do projeto, vá para **APIs e Serviços** → **Biblioteca**
2. Procure e ative as seguintes APIs:
   - **Google+ API** (ou People API)
   - **OAuth2 API**

### 3. Configurar Tela de Consentimento OAuth

1. Vá para **APIs e Serviços** → **Tela de consentimento OAuth**
2. Escolha **Externo** (para uso geral) ou **Interno** (apenas para sua organização)
3. Preencha as informações obrigatórias:
   - **Nome do aplicativo**: HostLink
   - **Email de suporte do usuário**: seu_email@gmail.com
   - **Domínios autorizados**: localhost (para desenvolvimento)
   - **Email de contato do desenvolvedor**: seu_email@gmail.com
4. Clique em "Salvar e continuar"
5. Em **Escopos**, adicione:
   - `../auth/userinfo.email`
   - `../auth/userinfo.profile`
   - `openid`
6. Continue até finalizar

### 4. Criar Credenciais OAuth 2.0

1. Vá para **APIs e Serviços** → **Credenciais**
2. Clique em "+ Criar credenciais" → "ID do cliente OAuth 2.0"
3. Configure:
   - **Tipo de aplicativo**: Aplicativo da Web
   - **Nome**: HostLink Web App
   - **URIs de redirecionamento autorizados**:
     - `http://localhost:5000/auth/callback` (desenvolvimento)
     - `https://seu-dominio.com/auth/callback` (produção, se aplicável)
4. Clique em "Criar"
5. **IMPORTANTE**: Copie e salve:
   - **ID do cliente** (Client ID)
   - **Chave secreta do cliente** (Client Secret)

### 5. Configurar Variáveis de Ambiente

1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edite o arquivo `.env` e adicione suas credenciais:
   ```env
   # Configurações do Google OAuth
   GOOGLE_CLIENT_ID=seu_client_id_aqui
   GOOGLE_CLIENT_SECRET=seu_client_secret_aqui
   GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback
   ```

### 6. Testar a Configuração

1. Reinicie o servidor:
   ```bash
   python web_app.py
   ```

2. Acesse: http://localhost:5000
3. Você deve ser redirecionado para a página de login
4. Clique em "Entrar com Google"
5. Autorize o aplicativo
6. Você deve ser redirecionado de volta e logado

## 🔒 Segurança

### Boas Práticas

- ✅ **Nunca commite** o arquivo `.env` no Git
- ✅ Use **chaves diferentes** para desenvolvimento e produção
- ✅ Configure **domínios autorizados** corretamente
- ✅ Revise **escopos** regularmente
- ✅ Monitore **logs de acesso**

### URLs de Redirecionamento

**Desenvolvimento:**
- `http://localhost:5000/auth/callback`
- `http://127.0.0.1:5000/auth/callback`

**Produção:**
- `https://seu-dominio.com/auth/callback`
- `https://www.seu-dominio.com/auth/callback`

## 🛠️ Solução de Problemas

### Erro: "Credenciais não configuradas"
```
⚠️ Credenciais do Google OAuth não configuradas
```
**Solução**: Verifique se `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` estão no arquivo `.env`

### Erro: "redirect_uri_mismatch"
```
Error 400: redirect_uri_mismatch
```
**Solução**: 
1. Verifique se a URL de callback está correta no Google Cloud Console
2. Certifique-se de que `GOOGLE_REDIRECT_URI` no `.env` corresponde exatamente

### Erro: "access_denied"
```
Error: access_denied
```
**Solução**: 
1. Verifique se a tela de consentimento está configurada
2. Certifique-se de que os escopos estão corretos
3. Verifique se o projeto está em modo de produção (se necessário)

### Erro: "invalid_client"
```
Error: invalid_client
```
**Solução**: 
1. Verifique se `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` estão corretos
2. Certifique-se de que as credenciais são do tipo "Aplicativo da Web"

## 📱 Funcionalidades Implementadas

### ✅ Login com Google
- Redirecionamento automático para Google
- Autorização OAuth 2.0
- Obtenção de perfil do usuário

### ✅ Sessão de Usuário
- Informações do usuário na navbar
- Foto de perfil (se disponível)
- Persistência da sessão

### ✅ Logout Seguro
- Limpeza da sessão
- Redirecionamento para login

### ✅ Proteção de Rotas
- Todas as páginas principais protegidas
- Redirecionamento automático para login
- Mensagens de feedback

## 🎯 Próximos Passos

1. **Configure as credenciais** seguindo este guia
2. **Teste o login** com sua conta Google
3. **Personalize** a tela de consentimento
4. **Configure produção** quando necessário

---

**💡 Dica**: Mantenha suas credenciais seguras e nunca as compartilhe publicamente!