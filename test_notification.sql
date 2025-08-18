-- Script para testar o sistema de notificações
-- Inserir uma notificação de teste

INSERT INTO notifications (
    user_id,
    type,
    title,
    message,
    is_read,
    created_at
) VALUES (
    1, -- Assumindo que existe um usuário com ID 1
    'new_booking',
    'Nova Reserva Recebida!',
    'Uma nova reserva de João Silva no dia 15/01/2025 até o dia 17/01/2025.',
    FALSE,
    NOW()
);

-- Verificar se a notificação foi criada
SELECT * FROM notifications WHERE user_id = 1 ORDER BY created_at DESC LIMIT 5;

-- Mensagem de confirmação
SELECT 'Notificação de teste criada com sucesso!' as message;