"""Servidor gRPC do gerenciador de tarefas.

Cada tarefa é gravada em um arquivo JSON separado, dentro da pasta de dados,
conforme a observação 4 do enunciado.
"""

import argparse
import os
import threading
import time
import uuid
from concurrent import futures
from datetime import datetime, timezone

import grpc
from google.protobuf import json_format

import tarefas_pb2
import tarefas_pb2_grpc


def agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RepositorioArquivos:
    """Persistência simples: um arquivo JSON por tarefa.

    O gRPC atende requisições em um pool de threads, então mais de uma
    chamada pode tocar o disco ao mesmo tempo. O lock evita leitura de
    arquivo pela metade durante uma escrita.
    """

    def __init__(self, pasta):
        self.pasta = pasta
        self._lock = threading.Lock()
        os.makedirs(self.pasta, exist_ok=True)

    def _caminho(self, id_tarefa):
        return os.path.join(self.pasta, f"{id_tarefa}.json")

    def salvar(self, tarefa):
        # MessageToJson converte a mensagem Protobuf em JSON. Aqui isso é só
        # conveniência de armazenamento: na rede, o que trafega é binário.
        texto = json_format.MessageToJson(tarefa, ensure_ascii=False)
        with self._lock:
            with open(self._caminho(tarefa.id), "w", encoding="utf-8") as f:
                f.write(texto)

    def carregar(self, id_tarefa):
        caminho = self._caminho(id_tarefa)
        with self._lock:
            if not os.path.exists(caminho):
                return None
            with open(caminho, encoding="utf-8") as f:
                texto = f.read()
        return json_format.Parse(texto, tarefas_pb2.Tarefa())

    def listar(self):
        with self._lock:
            nomes = sorted(n for n in os.listdir(self.pasta) if n.endswith(".json"))
        resultado = []
        for nome in nomes:
            tarefa = self.carregar(nome[:-5])
            if tarefa is not None:
                resultado.append(tarefa)
        return resultado

    def remover(self, id_tarefa):
        with self._lock:
            caminho = self._caminho(id_tarefa)
            if not os.path.exists(caminho):
                return False
            os.remove(caminho)
            return True


class ServicoTarefas(tarefas_pb2_grpc.GerenciadorTarefasServicer):
    """Implementa os métodos declarados no bloco `service` do .proto.

    A classe base GerenciadorTarefasServicer foi gerada pelo protoc. Cada
    método recebe a mensagem de requisição já desserializada e um `context`,
    que serve para devolver erros com código padronizado.
    """

    def __init__(self, repositorio):
        self.repo = repositorio

    def CriarTarefa(self, request, context):
        if not request.titulo.strip():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "titulo é obrigatório")

        tarefa = tarefas_pb2.Tarefa(
            id=str(uuid.uuid4()),
            titulo=request.titulo,
            descricao=request.descricao,
            status=request.status or tarefas_pb2.STATUS_PENDENTE,
            data_limite=request.data_limite,
            responsaveis=request.responsaveis,
            criada_em=agora(),
            atualizada_em=agora(),
        )
        self.repo.salvar(tarefa)
        print(f"[criar]  {tarefa.id}  {tarefa.titulo}", flush=True)
        return tarefas_pb2.CriarTarefaResponse(tarefa=tarefa)

    def ListarTarefas(self, request, context):
        tarefas = self.repo.listar()
        if request.filtro_status != tarefas_pb2.STATUS_INDEFINIDO:
            tarefas = [t for t in tarefas if t.status == request.filtro_status]
        print(f"[listar] {len(tarefas)} tarefa(s)", flush=True)
        return tarefas_pb2.ListarTarefasResponse(tarefas=tarefas, total=len(tarefas))

    def AtualizarTarefa(self, request, context):
        nova = request.tarefa
        if not nova.id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id é obrigatório")

        atual = self.repo.carregar(nova.id)
        if atual is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"tarefa {nova.id} não existe")

        # Só sobrescreve o que veio preenchido, preservando o resto.
        if nova.titulo:
            atual.titulo = nova.titulo
        if nova.descricao:
            atual.descricao = nova.descricao
        if nova.status != tarefas_pb2.STATUS_INDEFINIDO:
            atual.status = nova.status
        if nova.data_limite:
            atual.data_limite = nova.data_limite
        if nova.responsaveis:
            del atual.responsaveis[:]
            atual.responsaveis.extend(nova.responsaveis)
        atual.atualizada_em = agora()

        self.repo.salvar(atual)
        print(f"[atualizar] {atual.id}", flush=True)
        return tarefas_pb2.AtualizarTarefaResponse(tarefa=atual)

    def DeletarTarefa(self, request, context):
        if not request.id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id é obrigatório")
        removida = self.repo.remover(request.id)
        if not removida:
            context.abort(grpc.StatusCode.NOT_FOUND, f"tarefa {request.id} não existe")
        print(f"[deletar] {request.id}", flush=True)
        return tarefas_pb2.DeletarTarefaResponse(removida=True, id=request.id)

    def AcompanharTarefas(self, request, context):
        """Server streaming: devolve uma tarefa por vez.

        O `yield` no lugar do `return` é a única diferença em relação a um
        método unário. O cliente começa a receber antes de a lista terminar.
        """
        for tarefa in self.repo.listar():
            if context.is_active() is False:
                return
            if (
                request.filtro_status != tarefas_pb2.STATUS_INDEFINIDO
                and tarefa.status != request.filtro_status
            ):
                continue
            yield tarefa
            time.sleep(0.3)  # só para o streaming ficar visível na demonstração


def main():
    parser = argparse.ArgumentParser(description="Servidor gRPC de tarefas")
    parser.add_argument("--porta", type=int, default=50051)
    parser.add_argument("--dados", default=os.environ.get("PASTA_DADOS", "dados"))
    args = parser.parse_args()

    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tarefas_pb2_grpc.add_GerenciadorTarefasServicer_to_server(
        ServicoTarefas(RepositorioArquivos(args.dados)), servidor
    )
    # insecure = sem TLS. Suficiente para a atividade; em produção usaria
    # add_secure_port com credenciais.
    servidor.add_insecure_port(f"0.0.0.0:{args.porta}")
    servidor.start()
    print(f"servidor ouvindo em 0.0.0.0:{args.porta} | dados em {args.dados}/", flush=True)
    servidor.wait_for_termination()


if __name__ == "__main__":
    main()
