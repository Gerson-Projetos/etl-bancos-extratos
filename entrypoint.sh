#!/bin/bash
set -e

# ==============================================================================
# Script de Entrada (Entrypoint) para o ETL com Cron no Docker
# ==============================================================================

CRON_SCHEDULE="${CRON_SCHEDULE:-0 3 * * *}"
RUN_ON_STARTUP="${RUN_ON_STARTUP:-true}"

echo "=============================================================================="
echo "  Iniciando container ETL Bancos Extratos"
echo "  Horário Cron programado: $CRON_SCHEDULE"
echo "  Executar imediatamente ao iniciar: $RUN_ON_STARTUP"
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

# Configura o crontab do root
# Redireciona a saída para /proc/1/fd/1 para que os logs apareçam no 'docker compose logs'
cat <<EOF > /app/crontab.txt
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

$CRON_SCHEDULE . /app/cron.env && cd /app && /usr/local/bin/python main.py > /proc/1/fd/1 2>&1
# Linha em branco obrigatória no final do crontab
EOF

crontab /app/crontab.txt
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Crontab configurado com sucesso:"
crontab -l

# Se solicitado, executa uma carga inicial logo na subida do container
if [ "$RUN_ON_STARTUP" = "true" ] || [ "$RUN_ON_STARTUP" = "1" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Executando carga inicial de inicialização (RUN_ON_STARTUP=true)..."
    (cd /app && /usr/local/bin/python main.py) || echo "[AVISO] Execução inicial finalizada com erros. O cron continuará ativo para os próximos agendamentos."
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Daemon do Cron em execução em primeiro plano. Aguardando próximos disparos..."

# Executa o comando passado para o container (padrão: cron -f)
exec "$@"
