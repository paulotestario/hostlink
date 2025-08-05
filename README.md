# 🏖️ Sistema de Análise de Preços - Hotel Mont Blanc Itacuruçá

Sistema automatizado para consultar preços do Airbnb em Itacuruçá (Hotel Mont Blanc) e verificar a previsão do tempo para sugerir preços adequados para finais de semana.

## 🚀 Funcionalidades

- ✅ Busca automática de preços no Airbnb para Itacuruçá
- ✅ Foco específico no Hotel Mont Blanc
- ✅ Consulta da previsão do tempo em tempo real
- ✅ Sugestão de preços baseada no clima e demanda de final de semana
- ✅ Análise de probabilidade de chuva
- ✅ Ajuste automático de preços (premium/desconto)

## 📋 Pré-requisitos

- Python 3.7 ou superior
- Conexão com a internet
- Dependências listadas em `requirements.txt`

## 🔧 Instalação

1. **Clone ou baixe os arquivos do projeto**

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Como Usar

### Uso Básico

```python
from airbnb_scraper import AirbnbClimateScraper

# Criar instância
scraper = AirbnbClimateScraper()

# Analisar preços para datas específicas
results = scraper.run_analysis('2025-08-08', '2025-08-10', adults=2)
```

### Executar Exemplo Completo

```bash
python exemplo_uso.py
```

### Consulta Rápida

```python
from exemplo_uso import consulta_rapida

# Consulta rápida para um final de semana
resultados = consulta_rapida('2025-08-08', '2025-08-10')
```

## 📊 Fatores de Ajuste de Preço

### 🎉 Final de Semana
- **+30%** para sexta, sábado e domingo

### 🌤️ Condições Climáticas
- **+15%** para dias ensolarados (< 20% chance de chuva)
- **Preço normal** para condições moderadas (20-70% chance de chuva)
- **-15%** para dias chuvosos (> 70% chance de chuva)

## 📈 Exemplo de Saída

```
🏨 Analisando preços para Itacuruçá - Hotel Mont Blanc
📅 Check-in: 2025-08-08 | Check-out: 2025-08-10
👥 Adultos: 2
==================================================

🔍 Buscando preços no Airbnb...
🌤️ Consultando previsão do tempo...

🏨 Hotel Mont Blanc
💰 Preço encontrado: R$ 250.00/noite
💡 Preço sugerido: R$ 325.00/noite
📊 Fator de ajuste: 1.3x
🌧️ Probabilidade média de chuva: 15.0%
📈 Justificativa: Premium por tempo bom
🎉 Final de semana detectado - preço premium aplicado

🌤️ Previsão do tempo detalhada:
  📅 2025-08-08: 10% chuva - Ensolarado
  📅 2025-08-09: 20% chuva - Ensolarado
  📅 2025-08-10: 15% chuva - Ensolarado
```

## 🔗 URLs de Referência

- **Airbnb Itacuruçá:** https://www.airbnb.com.br/s/Itacuru%C3%A7%C3%A1--Mangaratiba/homes
- **Clima Tempo:** https://www.climatempo.com.br/previsao-do-tempo/15-dias/cidade/3211/itacuruca-rj

## 📝 Estrutura do Projeto

```
Airbnb/
├── airbnb_scraper.py      # Classe principal do scraper
├── exemplo_uso.py         # Exemplos de uso
├── requirements.txt       # Dependências
└── README.md             # Este arquivo
```

## ⚠️ Observações Importantes

1. **Rate Limiting:** O sistema inclui delays para evitar sobrecarga dos servidores
2. **Dados Dinâmicos:** Preços e clima são consultados em tempo real
3. **Fallback:** Se não encontrar dados específicos do Mont Blanc, usa preços médios da região
4. **Conexão:** Requer conexão estável com a internet

## 🛠️ Personalização

Você pode ajustar os fatores de preço editando a função `suggest_pricing()` em `airbnb_scraper.py`:

```python
# Fator final de semana
if is_weekend:
    price_multiplier *= 1.3  # Altere aqui o multiplicador

# Fator clima
if avg_rain_prob > 70:
    price_multiplier *= 0.85  # Altere o desconto por chuva
elif avg_rain_prob < 20:
    price_multiplier *= 1.15  # Altere o premium por tempo bom
```

## 🤝 Suporte

Para dúvidas ou problemas:
1. Verifique sua conexão com a internet
2. Confirme se as dependências estão instaladas
3. Execute o exemplo básico primeiro

---

**Desenvolvido para otimizar preços de hospedagem baseado em dados reais de mercado e clima** 🏖️