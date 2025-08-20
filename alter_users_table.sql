-- =====================================================
-- ALTER TABLE para adicionar autenticação por senha
-- Execute este script no SQL Editor do Supabase
-- =====================================================

-- Adicionar colunas para autenticação por senha
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_type VARCHAR(20) DEFAULT 'google';
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;

-- Modificar google_id para permitir NULL (para usuários sem Google)
ALTER TABLE users ALTER COLUMN google_id DROP NOT NULL;

-- Adicionar constraint para garantir que pelo menos um método de auth existe
ALTER TABLE users ADD CONSTRAINT check_auth_method 
    CHECK (
        (google_id IS NOT NULL AND auth_type = 'google') OR 
        (password_hash IS NOT NULL AND auth_type = 'email')
    );

-- Criar índice para email (para login rápido)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_auth_type ON users(auth_type);

-- Comentários para documentação
COMMENT ON COLUMN users.password_hash IS 'Hash da senha para autenticação por email';
COMMENT ON COLUMN users.auth_type IS 'Tipo de autenticação: google ou email';
COMMENT ON COLUMN users.email_verified IS 'TRUE se o email foi verificado';
COMMENT ON COLUMN users.verification_token IS 'Token para verificação de email';
COMMENT ON COLUMN users.reset_token IS 'Token para reset de senha';
COMMENT ON COLUMN users.reset_token_expires IS 'Data de expiração do token de reset';

-- Mensagem de confirmação
SELECT 'Tabela users atualizada com suporte a autenticação por email!' as status;