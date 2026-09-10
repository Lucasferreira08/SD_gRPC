# Gerenciador de tarefas com gRPC e Protocol Buffers

Sistema cliente-servidor em Python. O servidor guarda cada tarefa em um
arquivo JSON separado; a comunicação é feita por gRPC sobre HTTP/2, com as
mensagens definidas em `tarefas.proto`.

Grupo: Pedro Lucas, Gerson, Rafael Emanuel e Yago

## Arquivos

| Arquivo | Papel |
|---|---|
| `tarefas.proto` | Modelagem das mensagens e da interface do serviço (IDL) |
| `servidor.py` | Implementação dos métodos RPC e persistência em arquivos |
| `cliente.py` | Aplicação de linha de comando que consome o serviço |
| `Dockerfile` | Imagem com as dependências e a geração dos stubs |
| `docker-compose.yml` | Um servidor e dois clientes em IPs distintos |

## Rodando sem Docker (desenvolvimento)

Requer **Python 3.12**. Os pinos do `requirements.txt` (`grpcio` e
`grpcio-tools` 1.66.1) publicam wheels só até `cp312`; no Python 3.13 o pip
tenta compilar do fonte e falha. Para usar 3.13, suba os dois para `1.66.2`,
a primeira versão com wheel `cp313` — o `protobuf==5.27.2` é `abi3` e serve
nos dois casos.

Criação do ambiente no Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

No Linux ou macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Com o ambiente ativado, o resto é igual nos dois:

```bash
pip install -r requirements.txt

# gera tarefas_pb2.py, tarefas_pb2.pyi e tarefas_pb2_grpc.py
python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. tarefas.proto

python servidor.py            # terminal 1, ouve em 0.0.0.0:50051
python cliente.py listar      # terminal 2, fala com localhost:50051
```

Os dois terminais precisam estar com o venv ativado. O servidor aceita
`--porta` e `--dados`; esta última também pode vir da variável de ambiente
`PASTA_DADOS`, que é como o `Dockerfile` aponta para `/app/dados`.

Refaça a geração dos stubs toda vez que o `.proto` mudar. Os arquivos
`*_pb2*.py` são artefatos de build e estão no `.gitignore`, junto com a
`.venv/` e a pasta `dados/`.

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

python cliente.py --servidor 172.28.0.10:50051 menu
```

```bash
# terminal B
docker compose exec cliente2 bash
hostname -i    # mostra 172.28.0.22

python cliente.py --servidor 172.28.0.10:50051 menu
```

Dentro dos containers o `--servidor` é **obrigatório**. O padrão do cliente é
`localhost:50051`, e dentro do `cliente1` isso aponta para o próprio
`cliente1`, que só roda `sleep infinity` — o resultado é
`UNAVAILABLE: Connection refused`. Em vez do IP, também funciona o nome do
serviço, que o DNS interno do Compose resolve: `--servidor servidor:50051`.

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
python cliente.py --servidor IP:PORTA menu           # interface interativa
```

O `--servidor` pertence ao parser principal, não ao subcomando, então ele vem
sempre **antes** de `criar`, `listar`, `menu` e companhia. Escrito na outra
ordem, `python cliente.py menu --servidor ...`, o argparse rejeita.

### Menu interativo

Para não precisar decorar os argumentos durante a demonstração, execute:

```bash
python cliente.py
```

Sem subcomando o cliente abre o menu; `python cliente.py menu` faz o mesmo
explicitamente. As duas formas usam o servidor padrão `localhost:50051`, o que
só serve rodando na máquina host — dentro de um container, acrescente o
`--servidor` como mostrado acima.

O menu guia a criação, listagem, atualização, exclusão e o streaming de
tarefas. Ele mostra as opções de status numeradas e valida a data limite no
formato `AAAA-MM-DD`, incluindo datas inexistentes ou passadas. Os comandos
documentados acima continuam disponíveis para uso em scripts ou diretamente
no terminal.
