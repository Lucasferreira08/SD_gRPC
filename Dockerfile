FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tarefas.proto servidor.py cliente.py ./

# Geração dos stubs a partir do .proto.
# Produz tarefas_pb2.py (as mensagens) e tarefas_pb2_grpc.py (stub do
# cliente + classe base do servidor).
RUN python -m grpc_tools.protoc -I. \
    --python_out=. \
    --pyi_out=. \
    --grpc_python_out=. \
    tarefas.proto

ENV PYTHONUNBUFFERED=1
ENV PASTA_DADOS=/app/dados

CMD ["python", "servidor.py"]
