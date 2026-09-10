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
from datetime import date, datetime

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
STATUS_POR_OPCAO = {
    "1": tarefas_pb2.STATUS_PENDENTE,
    "2": tarefas_pb2.STATUS_EM_ANDAMENTO,
    "3": tarefas_pb2.STATUS_CONCLUIDA,
    "4": tarefas_pb2.STATUS_CANCELADA,
}
ROTULO_POR_STATUS = {
    tarefas_pb2.STATUS_PENDENTE: "Pendente",
    tarefas_pb2.STATUS_EM_ANDAMENTO: "Em andamento",
    tarefas_pb2.STATUS_CONCLUIDA: "Concluída",
    tarefas_pb2.STATUS_CANCELADA: "Cancelada",
}


def ler_status(mensagem, permitir_vazio=False, rotulo_vazio="Manter status atual"):
    """Exibe as opções de status e devolve o valor do enum Protobuf."""
    while True:
        print(f"\n{mensagem}")
        if permitir_vazio:
            print(f"[0] {rotulo_vazio}")
        for opcao, status in STATUS_POR_OPCAO.items():
            print(f"[{opcao}] {ROTULO_POR_STATUS[status]}")

        valor = input("Escolha uma opção: ").strip()
        if valor == "0" and permitir_vazio:
            return tarefas_pb2.STATUS_INDEFINIDO
        if valor in STATUS_POR_OPCAO:
            return STATUS_POR_OPCAO[valor]
        print("Opção inválida. Escolha um dos números mostrados.")


def ler_responsaveis(mensagem):
    valor = input(mensagem).strip()
    return [nome.strip() for nome in valor.split(",") if nome.strip()]


def ler_data(mensagem, permitir_vazio=True):
    """Lê uma data limite válida, no formato ISO e sem datas passadas."""
    while True:
        valor = input(mensagem).strip()
        if not valor and permitir_vazio:
            return ""
        try:
            data_limite = datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            print("Data inválida. Use o formato AAAA-MM-DD (ex.: 2026-10-15).")
            continue
        if data_limite < date.today():
            print("A data limite não pode estar no passado.")
            continue
        return valor


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
    sub = p.add_subparsers(dest="comando")

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

    sub.add_parser("menu", help="abre o menu interativo")

    return p


def menu_interativo(stub):
    """Interface guiada para usar o mesmo serviço gRPC sem decorar comandos."""
    while True:
        print("\n" + "=" * 42)
        print("        GERENCIADOR DE TAREFAS")
        print("=" * 42)
        print("[1] Criar tarefa")
        print("[2] Listar tarefas")
        print("[3] Atualizar tarefa")
        print("[4] Excluir tarefa")
        print("[5] Acompanhar tarefas (streaming)")
        print("[0] Sair")

        try:
            opcao = input("\nEscolha uma opção: ").strip()
            if opcao == "0":
                print("Até logo!")
                return

            if opcao == "1":
                titulo = input("Título: ").strip()
                if not titulo:
                    print("O título é obrigatório.")
                    continue
                descricao = input("Descrição (opcional): ").strip()
                status = ler_status("Status")
                data_limite = ler_data("Data limite, AAAA-MM-DD (opcional): ")
                responsaveis = ler_responsaveis(
                    "Responsáveis separados por vírgula (opcional): "
                )
                resposta = stub.CriarTarefa(tarefas_pb2.CriarTarefaRequest(
                    titulo=titulo,
                    descricao=descricao,
                    status=status,
                    data_limite=data_limite,
                    responsaveis=responsaveis,
                ))
                print("\nTarefa criada:\n" + formatar(resposta.tarefa))

            elif opcao == "2":
                filtro = ler_status(
                    "Filtrar por status",
                    permitir_vazio=True,
                    rotulo_vazio="Todas as tarefas",
                )
                resposta = stub.ListarTarefas(
                    tarefas_pb2.ListarTarefasRequest(filtro_status=filtro)
                )
                print(f"\n{resposta.total} tarefa(s)")
                for tarefa in resposta.tarefas:
                    print("\n" + formatar(tarefa))

            elif opcao == "3":
                id_tarefa = input("ID da tarefa: ").strip()
                if not id_tarefa:
                    print("O ID é obrigatório.")
                    continue
                print("Deixe em branco os campos que não deseja alterar.")
                tarefa = tarefas_pb2.Tarefa(
                    id=id_tarefa,
                    titulo=input("Novo título: ").strip(),
                    descricao=input("Nova descrição: ").strip(),
                    data_limite=ler_data("Nova data limite (AAAA-MM-DD): "),
                    responsaveis=ler_responsaveis(
                        "Novos responsáveis, separados por vírgula: "
                    ),
                )
                tarefa.status = ler_status(
                    "Novo status",
                    permitir_vazio=True,
                )
                resposta = stub.AtualizarTarefa(
                    tarefas_pb2.AtualizarTarefaRequest(tarefa=tarefa)
                )
                print("\nTarefa atualizada:\n" + formatar(resposta.tarefa))

            elif opcao == "4":
                id_tarefa = input("ID da tarefa a excluir: ").strip()
                confirmar = input("Confirma a exclusão? (s/N): ").strip().lower()
                if confirmar not in {"s", "sim"}:
                    print("Exclusão cancelada.")
                    continue
                resposta = stub.DeletarTarefa(
                    tarefas_pb2.DeletarTarefaRequest(id=id_tarefa)
                )
                print(f"Tarefa removida: {resposta.id}")

            elif opcao == "5":
                filtro = ler_status(
                    "Filtrar por status",
                    permitir_vazio=True,
                    rotulo_vazio="Todas as tarefas",
                )
                print("\nRecebendo tarefas do servidor:\n")
                for tarefa in stub.AcompanharTarefas(
                    tarefas_pb2.ListarTarefasRequest(filtro_status=filtro)
                ):
                    print(formatar(tarefa) + "\n")

            else:
                print("Opção inválida. Informe um número de 0 a 5.")

        except grpc.RpcError as erro:
            print(f"Erro do servidor [{erro.code().name}]: {erro.details()}")
        except (EOFError, KeyboardInterrupt):
            print("\nMenu encerrado.")
            return


def executar(stub, args):
    if args.comando == "menu":
        menu_interativo(stub)

    elif args.comando == "criar":
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
    # Sem subcomando, abre a interface guiada. Os subcomandos continuam
    # disponíveis para automação e para os exemplos da documentação.
    if args.comando is None:
        args.comando = "menu"
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
