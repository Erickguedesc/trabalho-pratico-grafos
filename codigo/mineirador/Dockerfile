# =============================================================
#  Minerador — coleta interações do GitHub e grava JSON
#  Imagem leve; roda uma vez e termina.
# =============================================================

FROM python:3.11-slim

# Metadados
LABEL maintainer="grupo-grafos-pucminas"
LABEL description="Minerador de interações GitHub → JSON"

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia só o necessário para instalar dependências primeiro
# (aproveita cache do Docker quando o código muda mas o requirements não)
COPY codigo/mineirador/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do minerador
COPY codigo/mineirador/ ./codigo/mineirador/

# Copia utilitários compartilhados (github_parser, etc.)
COPY codigo/utils/ ./codigo/utils/

# Garante que Python enxerga os módulos pelo caminho correto
ENV PYTHONPATH=/app

# Variáveis de ambiente esperadas (preenchidas pelo docker-compose)
ENV GITHUB_TOKEN=""
ENV OWNER=""
ENV REPO=""
ENV OUTPUT_DIR="/dados"

# Volume onde o JSON será gravado
VOLUME ["/dados"]

# Ponto de entrada — executa o minerador e termina
CMD ["python", "-m", "codigo.mineirador.miner"]