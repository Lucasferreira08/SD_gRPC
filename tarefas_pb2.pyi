from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STATUS_INDEFINIDO: _ClassVar[Status]
    STATUS_PENDENTE: _ClassVar[Status]
    STATUS_EM_ANDAMENTO: _ClassVar[Status]
    STATUS_CONCLUIDA: _ClassVar[Status]
    STATUS_CANCELADA: _ClassVar[Status]
STATUS_INDEFINIDO: Status
STATUS_PENDENTE: Status
STATUS_EM_ANDAMENTO: Status
STATUS_CONCLUIDA: Status
STATUS_CANCELADA: Status

class Tarefa(_message.Message):
    __slots__ = ("id", "titulo", "descricao", "status", "data_limite", "responsaveis", "criada_em", "atualizada_em")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITULO_FIELD_NUMBER: _ClassVar[int]
    DESCRICAO_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DATA_LIMITE_FIELD_NUMBER: _ClassVar[int]
    RESPONSAVEIS_FIELD_NUMBER: _ClassVar[int]
    CRIADA_EM_FIELD_NUMBER: _ClassVar[int]
    ATUALIZADA_EM_FIELD_NUMBER: _ClassVar[int]
    id: str
    titulo: str
    descricao: str
    status: Status
    data_limite: str
    responsaveis: _containers.RepeatedScalarFieldContainer[str]
    criada_em: str
    atualizada_em: str
    def __init__(self, id: _Optional[str] = ..., titulo: _Optional[str] = ..., descricao: _Optional[str] = ..., status: _Optional[_Union[Status, str]] = ..., data_limite: _Optional[str] = ..., responsaveis: _Optional[_Iterable[str]] = ..., criada_em: _Optional[str] = ..., atualizada_em: _Optional[str] = ...) -> None: ...

class CriarTarefaRequest(_message.Message):
    __slots__ = ("titulo", "descricao", "status", "data_limite", "responsaveis")
    TITULO_FIELD_NUMBER: _ClassVar[int]
    DESCRICAO_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DATA_LIMITE_FIELD_NUMBER: _ClassVar[int]
    RESPONSAVEIS_FIELD_NUMBER: _ClassVar[int]
    titulo: str
    descricao: str
    status: Status
    data_limite: str
    responsaveis: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, titulo: _Optional[str] = ..., descricao: _Optional[str] = ..., status: _Optional[_Union[Status, str]] = ..., data_limite: _Optional[str] = ..., responsaveis: _Optional[_Iterable[str]] = ...) -> None: ...

class CriarTarefaResponse(_message.Message):
    __slots__ = ("tarefa",)
    TAREFA_FIELD_NUMBER: _ClassVar[int]
    tarefa: Tarefa
    def __init__(self, tarefa: _Optional[_Union[Tarefa, _Mapping]] = ...) -> None: ...

class ListarTarefasRequest(_message.Message):
    __slots__ = ("filtro_status",)
    FILTRO_STATUS_FIELD_NUMBER: _ClassVar[int]
    filtro_status: Status
    def __init__(self, filtro_status: _Optional[_Union[Status, str]] = ...) -> None: ...

class ListarTarefasResponse(_message.Message):
    __slots__ = ("tarefas", "total")
    TAREFAS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    tarefas: _containers.RepeatedCompositeFieldContainer[Tarefa]
    total: int
    def __init__(self, tarefas: _Optional[_Iterable[_Union[Tarefa, _Mapping]]] = ..., total: _Optional[int] = ...) -> None: ...

class AtualizarTarefaRequest(_message.Message):
    __slots__ = ("tarefa",)
    TAREFA_FIELD_NUMBER: _ClassVar[int]
    tarefa: Tarefa
    def __init__(self, tarefa: _Optional[_Union[Tarefa, _Mapping]] = ...) -> None: ...

class AtualizarTarefaResponse(_message.Message):
    __slots__ = ("tarefa",)
    TAREFA_FIELD_NUMBER: _ClassVar[int]
    tarefa: Tarefa
    def __init__(self, tarefa: _Optional[_Union[Tarefa, _Mapping]] = ...) -> None: ...

class DeletarTarefaRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class DeletarTarefaResponse(_message.Message):
    __slots__ = ("removida", "id")
    REMOVIDA_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    removida: bool
    id: str
    def __init__(self, removida: bool = ..., id: _Optional[str] = ...) -> None: ...
