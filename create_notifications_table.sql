-- Script para criar tabela de notificações
-- Execute este script no editor SQL do Supabase

-- Tabela de notificações
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'new_booking', 'booking_cancelled', 'payment_received', etc.
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    related_booking_id INTEGER REFERENCES listing_bookings(id) ON DELETE CASCADE,
    related_listing_id INTEGER REFERENCES user_listings(id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP NULL
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Comentários para documentação
COMMENT ON TABLE notifications IS 'Tabela para gerenciar notificações dos usuários';
COMMENT ON COLUMN notifications.type IS 'Tipo da notificação: new_booking, booking_cancelled, payment_received, etc.';
COMMENT ON COLUMN notifications.is_read IS 'TRUE = notificação foi visualizada, FALSE = não visualizada';
COMMENT ON COLUMN notifications.read_at IS 'Timestamp de quando a notificação foi marcada como lida';

-- Mensagem de confirmação
SELECT 'Tabela de notificações criada com sucesso!' as message;