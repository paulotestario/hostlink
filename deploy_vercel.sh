#!/bin/bash
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
