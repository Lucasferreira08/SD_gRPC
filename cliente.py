"""Cliente gRPC em linha de comando.

Exemplos:
    python cliente.py --servidor 172.28.0.10:50051 criar \
        --titulo "Escrever o .proto" --responsavel ana --responsavel bruno
    python cliente.py --servidor 172.28.0.10:50051 listar
    python cliente.py --servidor 172.28.0.10:50051 atualizar --id <uuid> --status concluida
    python cliente.py --servidor 172.28.0.10:50051 deletar --id <uuid>
    python cliente.py --servidor 172.28.0.10:50051 acompanhar
"""

import argparse
import sys

import grpc

import tarefas_pb2
import tarefas_pb2_grpc

STATUS_POR_NOME = {
    "pendente": tarefas_pb2.STATUS_PENDENTE,
    "andamento": tarefas_pb2.STATUS_EM_ANDAMENTO,
    "concluida": tarefas_pb2.STATUS_CONCLUIDA,
    "cancelada": tarefas_pb2.STATUS_CANCELADA,
}
NOME_POR_STATUS = {v: k for k, v in STATUS_POR_NOME.items()}


def formatar(tarefa):
    responsaveis = ", ".join(tarefa.responsaveis) or "-"
    status = NOME_POR_STATUS.get(tarefa.status, "indefinido")
    return (
        f"{tarefa.id}\n"
        f"  título       : {tarefa.titulo}\n"
        f"  descrição    : {tarefa.descricao or '-'}\n"
        f"  status       : {status}\n"
        f"  data limite  : {tarefa.data_limite or '-'}\n"
        f"  responsáveis : {responsaveis}\n"
        f"  atualizada em: {tarefa.atualizada_em}"
    )


def montar_parser():
    p = argparse.ArgumentParser(description="Cliente gRPC de tarefas")
    p.add_argument("--servidor", default="localhost:50051",
                   help="endereço ip:porta do servidor")
    sub = p.add_subparsers(dest="comando", required=True)

    criar = sub.add_parser("criar")
    criar.add_argument("--titulo", required=True)
    criar.add_argument("--descricao", default="")
    criar.add_argument("--status", choices=list(STATUS_POR_NOME), default="pendente")
    criar.add_argument("--data-limite", default="")
    criar.add_argument("--responsavel", action="append", default=[],
                       help="pode repetir para vários responsáveis")

    listar = sub.add_parser("listar")
    listar.add_argument("--status", choices=list(STATUS_POR_NOME))

    atualizar = sub.add_parser("atualizar")
    atualizar.add_argument("--id", required=True)
    atualizar.add_argument("--titulo", default="")
    atualizar.add_argument("--descricao", default="")
    atualizar.add_argument("--status", choices=list(STATUS_POR_NOME))
    atualizar.add_argument("--data-limite", default="")
    atualizar.add_argument("--responsavel", action="append", default=[])

    deletar = sub.add_parser("deletar")
    deletar.add_argument("--id", required=True)

    acompanhar = sub.add_parser("acompanhar")
    acompanhar.add_argument("--status", choices=list(STATUS_POR_NOME))

    return p


def executar(stub, args):
    if args.comando == "criar":
        resp = stub.CriarTarefa(tarefas_pb2.CriarTarefaRequest(
            titulo=args.titulo,
            descricao=args.descricao,
            status=STATUS_POR_NOME[args.status],
            data_limite=args.data_limite,
            responsaveis=args.responsavel,
        ))
        print("tarefa criada:")
        print(formatar(resp.tarefa))

    elif args.comando == "listar":
        filtro = STATUS_POR_NOME.get(args.status, tarefas_pb2.STATUS_INDEFINIDO)
        resp = stub.ListarTarefas(tarefas_pb2.ListarTarefasRequest(filtro_status=filtro))
        print(f"{resp.total} tarefa(s)\n")
        for tarefa in resp.tarefas:
            print(formatar(tarefa))
            print()

    elif args.comando == "atualizar":
        tarefa = tarefas_pb2.Tarefa(
            id=args.id,
            titulo=args.titulo,
            descricao=args.descricao,
            data_limite=args.data_limite,
            responsaveis=args.responsavel,
        )
        if args.status:
            tarefa.status = STATUS_POR_NOME[args.status]
        resp = stub.AtualizarTarefa(tarefas_pb2.AtualizarTarefaRequest(tarefa=tarefa))
        print("tarefa atualizada:")
        print(formatar(resp.tarefa))

    elif args.comando == "deletar":
        resp = stub.DeletarTarefa(tarefas_pb2.DeletarTarefaRequest(id=args.id))
        print(f"removida: {resp.id}")

    elif args.comando == "acompanhar":
        filtro = STATUS_POR_NOME.get(args.status, tarefas_pb2.STATUS_INDEFINIDO)
        # A resposta é um iterador: cada volta do for é uma mensagem que
        # acabou de chegar pela rede.
        for tarefa in stub.AcompanharTarefas(
            tarefas_pb2.ListarTarefasRequest(filtro_status=filtro)
        ):
            print(formatar(tarefa))
            print()


def main():
    args = montar_parser().parse_args()
    # O canal é a conexão HTTP/2 com o servidor. O stub é o objeto que
    # expõe os métodos do .proto como se fossem funções locais.
    with grpc.insecure_channel(args.servidor) as canal:
        stub = tarefas_pb2_grpc.GerenciadorTarefasStub(canal)
        try:
            executar(stub, args)
        except grpc.RpcError as erro:
            print(f"erro do servidor [{erro.code().name}]: {erro.details()}",
                  file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
