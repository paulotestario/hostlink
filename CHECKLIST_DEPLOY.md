# ✅ Checklist de Deploy - HostLink

## 🎯 Pré-Deploy

### Banco de Dados
- [ ] Conta Supabase criada
- [ ] Projeto Supabase configurado
- [ ] Script `scripts_tabela_anuncios.sql` executado
- [ ] Script `alter_diferenca_anuncios.sql` executado
- [ ] Script `insert_municipios_rj.sql` executado
- [ ] Políticas RLS configuradas (opcional)

### Google OAuth
- [ ] Projeto Google Cloud criado
- [ ] API Google+ habilitada
- [ ] Credenciais OAuth 2.0 criadas
- [ ] URLs de redirecionamento configuradas

### Código
- [ ] Repositório Git inicializado
- [ ] Código commitado
- [ ] Arquivo `.env.production` configurado
- [ ] Health check testado localmente

## 🚀 Deploy

### Opção A: Vercel (Serverless)
- [ ] Vercel CLI instalado: `npm install -g vercel`
- [ ] Login no Vercel: `vercel login`
- [ ] Deploy executado: `vercel --prod`
- [ ] Variáveis de ambiente configuradas no dashboard
- [ ] URL de produção testada
- [ ] Health check funcionando: `https://seu-app.vercel.app/health`

### Opção B: Render.com (Servidor)
- [ ] Repositório no GitHub
- [ ] Remote Git configurado
- [ ] Código enviado: `git push origin main`
- [ ] Conta Render.com criada
- [ ] Web Service criado
- [ ] Repositório conectado
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy executado
- [ ] URL de produção testada

### Opção C: Railway.app
- [ ] Conta Railway criada
- [ ] Repositório conectado
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy executado
- [ ] URL de produção testada

## ⚙️ Configuração de Produção

### Variáveis de Ambiente
- [ ] `FLASK_SECRET_KEY` - Chave gerada automaticamente
- [ ] `FLASK_ENV=production`
- [ ] `SUPABASE_URL` - URL do seu projeto
- [ ] `SUPABASE_KEY` - Chave anon/public
- [ ] `GOOGLE_CLIENT_ID` - ID do OAuth
- [ ] `GOOGLE_CLIENT_SECRET` - Secret do OAuth
- [ ] `GOOGLE_REDIRECT_URI` - URL de callback de produção
- [ ] `EMAIL_USER` - Email para notificações (opcional)
- [ ] `EMAIL_PASSWORD` - Senha do app Gmail (opcional)
- [ ] `EMAIL_RECIPIENT` - Destinatário (opcional)

### URLs de Redirecionamento OAuth
- [ ] Desenvolvimento: `http://localhost:5000/auth/callback`
- [ ] Produção: `https://seu-dominio.com/auth/callback`

## 🧪 Testes Pós-Deploy

### Endpoints Básicos
- [ ] Página inicial: `https://seu-dominio.com/`
- [ ] Health check: `https://seu-dominio.com/health`
- [ ] Login: `https://seu-dominio.com/login`
- [ ] Perfil: `https://seu-dominio.com/perfil`
- [ ] Análise: `https://seu-dominio.com/analise`

### Funcionalidades
- [ ] Login com Google funciona
- [ ] Cadastro de anúncios funciona
- [ ] Extração de dados do Airbnb funciona
- [ ] Análise de mercado funciona
- [ ] Salvamento no banco funciona

### Performance
- [ ] Tempo de resposta < 5s
- [ ] Health check retorna status 200
- [ ] Sem erros 500 nos logs
- [ ] SSL funcionando (HTTPS)

## 📊 Monitoramento

### Para Vercel (Serverless)
- [ ] Cron job externo configurado
- [ ] URL de monitoramento: `https://seu-dominio.com/api/monitor`
- [ ] Frequência: a cada 5 minutos
- [ ] Logs de monitoramento verificados

### Para Render/Railway (Servidor)
- [ ] Monitoramento automático ativo
- [ ] Logs de monitoramento verificados
- [ ] Uptime monitor configurado (opcional)

### Ferramentas Externas (Opcional)
- [ ] UptimeRobot configurado
- [ ] Google Analytics adicionado
- [ ] Sentry para error tracking

## 🔧 Configurações Avançadas (Opcional)

### Domínio Personalizado
- [ ] Domínio registrado
- [ ] DNS configurado
- [ ] SSL certificado
- [ ] Redirecionamento HTTPS

### Cache e Performance
- [ ] Redis configurado (se disponível)
- [ ] CDN configurado
- [ ] Compressão gzip habilitada
- [ ] Minificação de assets

### Backup e Segurança
- [ ] Backup automático do Supabase
- [ ] Políticas de segurança RLS
- [ ] Rate limiting configurado
- [ ] Logs de auditoria

## 🆘 Troubleshooting

### Problemas Comuns
- [ ] Erro 500: Verificar logs e variáveis de ambiente
- [ ] OAuth não funciona: Verificar URLs de redirecionamento
- [ ] Banco não conecta: Verificar credenciais Supabase
- [ ] Timeout: Otimizar consultas ou mudar plataforma
- [ ] Cold start lento: Considerar warming ou servidor persistente

### Logs e Debug
- [ ] Logs da aplicação verificados
- [ ] Logs do banco verificados
- [ ] Métricas de performance analisadas
- [ ] Erros corrigidos

## 📞 Suporte

### Documentação
- [ ] `DEPLOY_PRODUCAO.md` - Guia completo
- [ ] `README.md` - Documentação geral
- [ ] `GOOGLE_OAUTH_SETUP.md` - Setup OAuth
- [ ] `SUPABASE_SETUP.md` - Setup banco

### Contatos
- [ ] Suporte Vercel: [vercel.com/support](https://vercel.com/support)
- [ ] Suporte Render: [render.com/docs](https://render.com/docs)
- [ ] Suporte Supabase: [supabase.com/docs](https://supabase.com/docs)
- [ ] Google Cloud: [cloud.google.com/support](https://cloud.google.com/support)

---

## 🎉 Deploy Concluído!

**Quando todos os itens estiverem marcados, seu HostLink estará rodando em produção!**

### URLs Importantes:
- **Aplicação**: https://seu-dominio.com
- **Health Check**: https://seu-dominio.com/health
- **Monitoramento**: https://seu-dominio.com/api/monitor
- **Dashboard Supabase**: https://app.supabase.com
- **Dashboard da Plataforma**: (Vercel/Render/Railway)

### Próximos Passos:
1. Configurar monitoramento de uptime
2. Implementar analytics
3. Configurar alertas de erro
4. Otimizar performance
5. Adicionar mais funcionalidades

**🚀 Parabéns! Seu HostLink está no ar!**