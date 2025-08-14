-- =====================================================
-- SCRIPT PARA CRIAR TABELA DE FAVORITOS
-- =====================================================

-- Criar tabela de favoritos do usuário
CREATE TABLE IF NOT EXISTS user_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    listing_id INTEGER REFERENCES user_listings(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Garantir que um usuário não pode favoritar o mesmo anúncio duas vezes
    UNIQUE(user_id, listing_id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_listing_id ON user_favorites(listing_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_created_at ON user_favorites(created_at);

-- Comentários sobre a tabela
COMMENT ON TABLE user_favorites IS 'Tabela para armazenar os anúncios favoritos dos usuários';
COMMENT ON COLUMN user_favorites.user_id IS 'ID do usuário que favoritou o anúncio';
COMMENT ON COLUMN user_favorites.listing_id IS 'ID do anúncio que foi favoritado';
COMMENT ON COLUMN user_favorites.created_at IS 'Data e hora quando o anúncio foi favoritado';
COMMENT ON COLUMN user_favorites.updated_at IS 'Data e hora da última atualização';

-- =====================================================
-- EXEMPLOS DE USO
-- =====================================================

/*
-- Adicionar um anúncio aos favoritos
INSERT INTO user_favorites (user_id, listing_id) 
VALUES (1, 5) 
ON CONFLICT (user_id, listing_id) DO NOTHING;

-- Remover um anúncio dos favoritos
DELETE FROM user_favorites 
WHERE user_id = 1 AND listing_id = 5;

-- Buscar todos os favoritos de um usuário
SELECT uf.*, ul.title, ul.url, ul.price_per_night, ul.rating
FROM user_favorites uf
JOIN user_listings ul ON uf.listing_id = ul.id
WHERE uf.user_id = 1
ORDER BY uf.created_at DESC;

-- Verificar se um anúncio é favorito de um usuário
SELECT EXISTS(
    SELECT 1 FROM user_favorites 
    WHERE user_id = 1 AND listing_id = 5
) AS is_favorite;

-- Contar quantos favoritos um usuário tem
SELECT COUNT(*) as total_favorites
FROM user_favorites
WHERE user_id = 1;

-- Buscar anúncios mais favoritados
SELECT ul.title, ul.url, COUNT(uf.id) as favorite_count
FROM user_listings ul
JOIN user_favorites uf ON ul.id = uf.listing_id
GROUP BY ul.id, ul.title, ul.url
ORDER BY favorite_count DESC
LIMIT 10;
*/