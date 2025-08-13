#!/bin/bash
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
