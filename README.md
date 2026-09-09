# Gerenciador de tarefas com gRPC e Protocol Buffers

Sistema cliente-servidor em Python. O servidor guarda cada tarefa em um
arquivo JSON separado; a comunicação é feita por gRPC sobre HTTP/2, com as
mensagens definidas em `tarefas.proto`.

## Arquivos

| Arquivo | Papel |
|---|---|
| `tarefas.proto` | Modelagem das mensagens e da interface do serviço (IDL) |
| `servidor.py` | Implementação dos métodos RPC e persistência em arquivos |
| `cliente.py` | Aplicação de linha de comando que consome o serviço |
| `Dockerfile` | Imagem com as dependências e a geração dos stubs |
| `docker-compose.yml` | Um servidor e dois clientes em IPs distintos |

## Rodando sem Docker (desenvolvimento)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# gera tarefas_pb2.py e tarefas_pb2_grpc.py
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. tarefas.proto

python servidor.py            # terminal 1
python cliente.py listar      # terminal 2
```

Refaça a geração dos stubs toda vez que o `.proto` mudar. Os arquivos
`*_pb2*.py` são artefatos de build e normalmente não vão para o repositório.

## Rodando com Docker (demonstração da Obs 2)

```bash
docker compose up -d --build
docker compose ps          # confirma os três containers de pé
```

Endereços atribuídos:

| Container | IP |
|---|---|
| servidor | 172.28.0.10 |
| cliente1 | 172.28.0.21 |
| cliente2 | 172.28.0.22 |

Abra dois terminais e entre em um cliente em cada um:

```bash
# terminal A
docker compose exec cliente1 bash
hostname -i    # mostra 172.28.0.21

python cliente.py --servidor 172.28.0.10:50051 criar \
  --titulo "Escrever o arquivo .proto" \
  --descricao "Definir mensagens e o bloco service" \
  --data-limite 2026-09-20 \
  --responsavel ana --responsavel bruno
```

```bash
# terminal B
docker compose exec cliente2 bash
hostname -i    # mostra 172.28.0.22

python cliente.py --servidor 172.28.0.10:50051 listar
```

O cliente 2 enxerga a tarefa criada pelo cliente 1 — é a prova de que o
estado vive no servidor. Deixe um terceiro terminal com
`docker compose logs -f servidor` para mostrar as chamadas chegando.

Para encerrar: `docker compose down`.

## Comandos do cliente

```bash
python cliente.py --servidor IP:PORTA criar --titulo "..." [--descricao "..."] \
    [--status pendente|andamento|concluida|cancelada] [--data-limite AAAA-MM-DD] \
    [--responsavel nome]...

python cliente.py --servidor IP:PORTA listar [--status ...]
python cliente.py --servidor IP:PORTA atualizar --id UUID [--titulo ...] [--status ...]
python cliente.py --servidor IP:PORTA deletar --id UUID
python cliente.py --servidor IP:PORTA acompanhar     # server streaming
```

## Roteiro sugerido para a apresentação (10 a 15 min)

1. **O `.proto` e a compilação** (3 min). Mostre o arquivo, aponte os números
   dos campos e explique que eles, não os nomes, são a identidade no formato
   binário. Rode o `protoc` ao vivo e abra o `tarefas_pb2_grpc.py` gerado para
   mostrar o `GerenciadorTarefasStub` e o `GerenciadorTarefasServicer`.

2. **Servidor e cliente** (4 min). No servidor, mostre a classe
   `ServicoTarefas` herdando da classe gerada e o uso de
   `context.abort(grpc.StatusCode.NOT_FOUND, ...)`. No cliente, mostre as duas
   linhas que constroem canal e stub, e destaque que o resto do código chama
   os métodos como se fossem locais.

3. **Demonstração distribuída** (4 min). Os três containers, os IPs distintos,
   um cliente criando e o outro listando. Termine com o comando `acompanhar`
   para mostrar o server streaming.

4. **Protobuf comparado a JSON** (3 min). Argumentos a usar:
   - o contrato é compilado, não documentado: erro de tipo aparece antes de
     rodar, não em produção;
   - serialização binária com campos identificados por número reduz o tamanho
     da mensagem e elimina o custo de interpretar texto;
   - evolução de esquema: acrescentar um campo novo não quebra clientes
     antigos, que ignoram o número desconhecido;
   - HTTP/2 dá multiplexação e streaming nativo;
   - o custo: não é legível por humanos e exige ferramenta específica
     (`grpcurl`) para inspecionar o tráfego.

   Para uma medida concreta, compare os tamanhos ao vivo:

   ```python
   import json
   from google.protobuf import json_format
   import tarefas_pb2

   t = tarefas_pb2.Tarefa(id="8f2b...", titulo="Escrever o .proto",
                          status=tarefas_pb2.STATUS_PENDENTE)
   binario = t.SerializeToString()
   texto = json_format.MessageToJson(t).encode()
   print(len(binario), len(texto))
   ```

## Ideias para ir além, se sobrar tempo

- Trocar `insecure_channel` por TLS com `grpc.ssl_channel_credentials()`.
- Um interceptor no servidor para registrar latência de cada chamada.
- Usar `google.protobuf.Timestamp` no lugar das datas como string.
- Um cliente em outra linguagem (Go ou Node) a partir do mesmo `.proto`, o que
  demonstra bem o valor da IDL.
