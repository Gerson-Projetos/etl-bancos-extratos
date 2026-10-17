#!/bin/bash
set -e

# ==============================================================================
# Script de Entrada (Entrypoint) para o ETL com Cron no Docker
# ==============================================================================

CRON_SCHEDULE="${CRON_SCHEDULE:-0 3 * * *}"
RUN_ON_STARTUP="${RUN_ON_STARTUP:-true}"
N8N_WEBHOOK_URL="${N8N_WEBHOOK_URL:-}" # URL do seu webhook no n8n

echo "=============================================================================="
echo "  Iniciando container ETL Bancos Extratos"
echo "  Horário Cron programado: $CRON_SCHEDULE"
echo "  Executar imediatamente ao iniciar: $RUN_ON_STARTUP"
if [ -n "$N8N_WEBHOOK_URL" ]; then
    echo "  Webhook n8n configurado: SIM"
else
    echo "  Webhook n8n configurado: NÃO"
fi
echo "=============================================================================="

# Exporta todas as variáveis de ambiente para /app/cron.env para que o cron
# tenha acesso às credenciais (DB_*, DRIVE_ID, etc.) sem perda de contexto
python3 -c "
import os
with open('/app/cron.env', 'w') as f:
    for k, v in os.environ.items():
        if k not in ['HOSTNAME', 'HOME', 'PWD', 'SHLVL', '_', 'OLDPWD']:
            f.write(f'export {k}={repr(v)}\n')
"
chmod 0600 /app/cron.env

# ------------------------------------------------------------------------------
# NOVO: Cria o script centralizado que roda o Python e avisa o n8n no final
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# NOVO: Cria o script centralizado que roda o Python e avisa o n8n no final
# ------------------------------------------------------------------------------
cat <<'EOF' > /app/run_etl.sh
#!/bin/bash
. /app/cron.env
cd /app

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando execução do ETL (main.py)..."

if /usr/local/bin/python main.py; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETL finalizado com SUCESSO."
    
    # Dispara o Webhook se a URL foi configurada no docker-compose
    if [ -n "$N8N_WEBHOOK_URL" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Notificando n8n..."
        /usr/local/bin/python -c "
import urllib.request, json, sys, datetime

try:
    url = sys.argv[1]
    dados = {
        'status': 'sucesso',
        'rotina': 'ETL Bancos Extratos',
        'horario': datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    req = urllib.request.Request(
        url, 
        data=json.dumps(dados).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    urllib.request.urlopen(req)
except Exception as e:
    print('Erro ao notificar n8n:', e)
" "$N8N_WEBHOOK_URL"
    fi
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERRO] Falha na execução do ETL."
    exit 1
fi
EOF

chmod +x /app/run_etl.sh

# ------------------------------------------------------------------------------

# Configura o crontab do root para apontar para o novo script
cat <<EOF > /app/crontab.txt
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

$CRON_SCHEDULE /app/run_etl.sh > /proc/1/fd/1 2>&1
# Linha em branco obrigatória no final do crontab
EOF

crontab /app/crontab.txt
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Crontab configurado com sucesso:"
crontab -l

# Se solicitado, executa uma carga inicial usando o novo script
if [ "$RUN_ON_STARTUP" = "true" ] || [ "$RUN_ON_STARTUP" = "1" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Executando carga inicial de inicialização (RUN_ON_STARTUP=true)..."
    /app/run_etl.sh || echo "[AVISO] Execução inicial finalizada com erros. O cron continuará ativo para os próximos agendamentos."
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Daemon do Cron em execução em primeiro plano. Aguardando próximos disparos..."

# Executa o comando passado para o container (padrão: cron -f)
exec "$@"