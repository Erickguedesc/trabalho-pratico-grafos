# =============================================================
#  App — demo CLI + interface Streamlit
#  Contém a biblioteca (grafos, builder, analysis) e a UI.
# =============================================================

FROM python:3.11-slim

# Metadados
LABEL maintainer="grupo-grafos-pucminas"
LABEL description="Aplicação principal — demo CLI e Streamlit"

# Diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para o Neo4j driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python primeiro (cache Docker)
COPY requirements-app.txt .

RUN pip install --no-cache-dir -r requirements-app.txt

# Copia toda a biblioteca e o app
COPY codigo/biblioteca/ ./codigo/biblioteca/
COPY codigo/app/        ./codigo/app/
COPY codigo/services/   ./codigo/services/
COPY codigo/utils/      ./codigo/utils/
COPY codigo/export/     ./codigo/export/

# Garante que Python enxerga os módulos
ENV PYTHONPATH=/app

# Variáveis de ambiente esperadas (preenchidas pelo docker-compose)
ENV INPUT_DIR="/dados"
ENV NEO4J_URI="bolt://neo4j:7687"
ENV NEO4J_USER="neo4j"
ENV NEO4J_PASSWORD="senha123"

# Volume onde lê o JSON gerado pelo minerador
VOLUME ["/dados"]

# Porta do Streamlit
EXPOSE 8501

# Streamlit precisa dessas configs para rodar em container
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Ponto de entrada — sobe o Streamlit
# Para usar só a CLI: docker exec grafos-app python -m codigo.app.demo_cli <cmd>
CMD ["streamlit", "run", "codigo/app/pages/app.py"]