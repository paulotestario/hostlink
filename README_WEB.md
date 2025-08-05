# 🌐 Interface Web - Análise de Preços Airbnb

## 📋 Visão Geral

A aplicação web oferece uma interface moderna e intuitiva para visualizar e gerenciar as análises de preços do Hotel Mont Blanc em Itacuruçá.

## 🚀 Como Usar

### 1. Iniciar a Aplicação
```bash
cd c:\Airbnb
py web_app.py
```

### 2. Acessar a Interface
Abra seu navegador e acesse: **http://localhost:5000**

## 🎯 Funcionalidades

### Dashboard Principal (`/`)
- **Nova Análise**: Execute análises sob demanda com datas personalizadas
- **Monitoramento Automático**: Ative/desative análises automáticas 2x ao dia
- **Resumo da Última Análise**: Visualize rapidamente os resultados mais recentes
- **Status em Tempo Real**: Acompanhe o status do monitoramento

### Análise Detalhada (`/analise`)
- **Métricas Principais**: Preço sugerido, previsão do tempo, fator de ajuste
- **Detalhes da Reserva**: Informações completas do período analisado
- **Análise da Concorrência**: Lista de propriedades concorrentes com preços
- **Gráficos Interativos**: Visualização de preços e histórico
- **Histórico de Análises**: Acompanhe a evolução dos preços ao longo do tempo

## 🔧 APIs Disponíveis

### Executar Análise
```
POST /api/run_analysis
{
  "checkin": "2025-08-08",
  "checkout": "2025-08-10",
  "adults": 2,
  "beachfront": true
}
```

### Iniciar Monitoramento
```
POST /api/start_monitoring
{
  "beachfront": true
}
```

### Parar Monitoramento
```
POST /api/stop_monitoring
```

### Obter Última Análise
```
GET /api/get_latest
```

### Obter Histórico
```
GET /api/get_history
```

## 📊 Recursos Visuais

### Gráficos
- **Gráfico de Barras**: Comparação entre preço original, sugerido e média da concorrência
- **Gráfico de Linha**: Evolução histórica dos preços e probabilidade de chuva

### Indicadores
- **Status do Monitoramento**: Indicador visual ativo/inativo
- **Previsão do Tempo**: Ícones dinâmicos baseados na probabilidade de chuva
- **Cards Interativos**: Hover effects e animações suaves

## 🎨 Interface

### Design Responsivo
- **Mobile-First**: Funciona perfeitamente em dispositivos móveis
- **Bootstrap 5**: Interface moderna e profissional
- **Font Awesome**: Ícones consistentes e intuitivos

### Cores e Temas
- **Gradiente Principal**: Azul para roxo (#667eea → #764ba2)
- **Cards Temáticos**: Cores específicas para diferentes tipos de informação
- **Feedback Visual**: Alertas coloridos para diferentes estados

## 🔄 Atualizações Automáticas

### Status em Tempo Real
- Verificação automática do status a cada 30 segundos
- Atualização dinâmica dos indicadores
- Notificações de mudanças de estado

### Monitoramento Contínuo
- Análises automáticas a cada 12 horas
- Armazenamento do histórico (últimas 50 análises)
- Envio de relatórios por email (configurável)

## 🛠️ Personalização

### Configurações Padrão
- **Datas**: Próximo final de semana automaticamente
- **Adultos**: 2 pessoas
- **Propriedade**: Beira-mar ativado

### Parâmetros Ajustáveis
- Período de análise
- Número de hóspedes
- Tipo de propriedade (beira-mar ou não)
- Frequência do monitoramento

## 📱 Compatibilidade

### Navegadores Suportados
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Dispositivos
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (320px - 767px)

## 🔒 Segurança

### Validações
- Validação de datas no frontend e backend
- Sanitização de inputs
- Tratamento de erros robusto

### Limitações
- Máximo 50 análises no histórico
- Rate limiting implícito via interface
- Validação de parâmetros obrigatórios

## 📈 Monitoramento

### Logs
- Logs detalhados no terminal
- Timestamps de todas as operações
- Indicação de sucesso/erro

### Performance
- Carregamento assíncrono
- Otimização de requests
- Cache de dados recentes

## 🎯 Próximos Passos

1. **Acesse a aplicação**: http://localhost:5000
2. **Execute uma análise**: Use o formulário na página principal
3. **Explore os detalhes**: Clique em "Ver Análise Detalhada"
4. **Ative o monitoramento**: Para análises automáticas
5. **Acompanhe o histórico**: Veja a evolução dos preços

---

**💡 Dica**: Mantenha a aplicação rodando para receber análises automáticas e acompanhar as mudanças de preços em tempo real!