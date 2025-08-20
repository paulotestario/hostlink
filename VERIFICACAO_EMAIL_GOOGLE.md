# Verificação de Email já Usado com Google

## 📋 Funcionalidade Implementada

Esta funcionalidade impede que usuários tentem criar contas ou fazer login por email/senha quando o email já está associado a uma conta Google, direcionando-os para usar a autenticação Google.

## 🔧 Implementação

### 1. Novo Método no Database (`database.py`)

```python
def check_email_auth_type(self, email: str) -> Optional[str]:
    """
    Verifica o tipo de autenticação usado por um email
    Retorna 'google', 'email' ou None se não encontrado
    """
```

**Lógica:**
- Busca o usuário pelo email
- Se tem `google_id` preenchido → retorna `'google'`
- Se tem `auth_type` definido → retorna o valor do campo
- Se não encontrado → retorna `None`

### 2. Verificação no Registro (`/register`)

**Antes:**
```python
if db and db.get_user_by_email(email):
    flash('Este email já está cadastrado.', 'error')
```

**Depois:**
```python
auth_type = db.check_email_auth_type(email)
if auth_type == 'google':
    flash('Este email já está cadastrado com conta Google. Por favor, faça login usando sua conta Google.', 'error')
elif auth_type == 'email':
    flash('Este email já está cadastrado.', 'error')
```

### 3. Verificação no Login por Email (`/auth/email`)

**Nova verificação adicionada:**
```python
auth_type = db.check_email_auth_type(email)
if auth_type == 'google':
    flash('Este email está associado a uma conta Google. Por favor, faça login usando sua conta Google.', 'error')
    return redirect(url_for('login'))
elif auth_type is None:
    flash('Email não encontrado. Verifique o email ou crie uma nova conta.', 'error')
    return redirect(url_for('login'))
```

## 🎯 Cenários de Uso

### Cenário 1: Registro com Email já Usado no Google
- **Situação:** Usuário tenta criar conta com email que já fez login via Google
- **Resultado:** Mensagem "Este email já está cadastrado com conta Google. Por favor, faça login usando sua conta Google."
- **Ação:** Usuário é direcionado a usar o botão "Login com Google"

### Cenário 2: Login por Email/Senha com Email do Google
- **Situação:** Usuário tenta fazer login por email/senha com email que está associado ao Google
- **Resultado:** Mensagem "Este email está associado a uma conta Google. Por favor, faça login usando sua conta Google."
- **Ação:** Usuário é redirecionado para a página de login

### Cenário 3: Email Não Encontrado
- **Situação:** Usuário tenta fazer login com email que não existe
- **Resultado:** Mensagem "Email não encontrado. Verifique o email ou crie uma nova conta."
- **Ação:** Usuário pode corrigir o email ou criar nova conta

### Cenário 4: Email já Cadastrado com Senha
- **Situação:** Usuário tenta registrar com email que já tem conta por senha
- **Resultado:** Mensagem "Este email já está cadastrado."
- **Ação:** Usuário deve fazer login com email/senha

## ✅ Teste Realizado

O arquivo `test_email_google_check.py` demonstra:

1. ✅ **Detecção de email Google:** Identifica corretamente emails associados a contas Google
2. ✅ **Email não existente:** Retorna `None` para emails não cadastrados
3. ✅ **Funcionamento da lógica:** A verificação funciona conforme esperado

## 🔒 Benefícios de Segurança

1. **Prevenção de Conflitos:** Evita que o mesmo email tenha múltiplas contas com diferentes métodos de autenticação
2. **Experiência Consistente:** Garante que usuários sempre usem o mesmo método de login
3. **Clareza para o Usuário:** Mensagens específicas orientam o usuário sobre qual método usar
4. **Integridade dos Dados:** Mantém a consistência do banco de dados

## 🚀 Como Usar

### Para Usuários:
1. Se você já fez login com Google, sempre use o botão "Login com Google"
2. Se você criou conta com email/senha, use o formulário de login
3. As mensagens de erro te orientarão sobre qual método usar

### Para Desenvolvedores:
1. A verificação é automática em ambas as rotas (`/register` e `/auth/email`)
2. O método `check_email_auth_type()` pode ser usado em outras partes do sistema
3. A lógica é robusta e trata casos edge (fallbacks)

## 📝 Arquivos Modificados

- `database.py`: Adicionado método `check_email_auth_type()`
- `web_app.py`: Atualizadas rotas `/register` e `/auth/email`
- `test_email_google_check.py`: Arquivo de teste criado

## 🎉 Resultado

Agora o sistema oferece uma experiência de autenticação mais robusta e user-friendly, evitando confusões sobre qual método de login usar e mantendo a integridade dos dados de usuário.