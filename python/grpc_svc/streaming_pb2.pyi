from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Usuario(_message.Message):
    __slots__ = ("id", "nome", "idade")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    IDADE_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    idade: int
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ..., idade: _Optional[int] = ...) -> None: ...

class Musica(_message.Message):
    __slots__ = ("id", "nome", "duracao_seg", "album_id", "genero_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    DURACAO_SEG_FIELD_NUMBER: _ClassVar[int]
    ALBUM_ID_FIELD_NUMBER: _ClassVar[int]
    GENERO_ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    duracao_seg: int
    album_id: int
    genero_id: int
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ..., duracao_seg: _Optional[int] = ..., album_id: _Optional[int] = ..., genero_id: _Optional[int] = ...) -> None: ...

class Playlist(_message.Message):
    __slots__ = ("id", "nome", "usuario_id", "musicas")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    USUARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MUSICAS_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    usuario_id: int
    musicas: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ..., usuario_id: _Optional[int] = ..., musicas: _Optional[_Iterable[int]] = ...) -> None: ...

class Genero(_message.Message):
    __slots__ = ("id", "nome")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ...) -> None: ...

class Artista(_message.Message):
    __slots__ = ("id", "nome", "pais")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    PAIS_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    pais: str
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ..., pais: _Optional[str] = ...) -> None: ...

class Album(_message.Message):
    __slots__ = ("id", "titulo", "ano", "artista_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITULO_FIELD_NUMBER: _ClassVar[int]
    ANO_FIELD_NUMBER: _ClassVar[int]
    ARTISTA_ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    titulo: str
    ano: int
    artista_id: int
    def __init__(self, id: _Optional[int] = ..., titulo: _Optional[str] = ..., ano: _Optional[int] = ..., artista_id: _Optional[int] = ...) -> None: ...

class Id(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class Vazio(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Pagina(_message.Message):
    __slots__ = ("pagina", "tamanho")
    PAGINA_FIELD_NUMBER: _ClassVar[int]
    TAMANHO_FIELD_NUMBER: _ClassVar[int]
    pagina: int
    tamanho: int
    def __init__(self, pagina: _Optional[int] = ..., tamanho: _Optional[int] = ...) -> None: ...

class Usuarios(_message.Message):
    __slots__ = ("usuarios",)
    USUARIOS_FIELD_NUMBER: _ClassVar[int]
    usuarios: _containers.RepeatedCompositeFieldContainer[Usuario]
    def __init__(self, usuarios: _Optional[_Iterable[_Union[Usuario, _Mapping]]] = ...) -> None: ...

class Musicas(_message.Message):
    __slots__ = ("musicas",)
    MUSICAS_FIELD_NUMBER: _ClassVar[int]
    musicas: _containers.RepeatedCompositeFieldContainer[Musica]
    def __init__(self, musicas: _Optional[_Iterable[_Union[Musica, _Mapping]]] = ...) -> None: ...

class Playlists(_message.Message):
    __slots__ = ("playlists",)
    PLAYLISTS_FIELD_NUMBER: _ClassVar[int]
    playlists: _containers.RepeatedCompositeFieldContainer[Playlist]
    def __init__(self, playlists: _Optional[_Iterable[_Union[Playlist, _Mapping]]] = ...) -> None: ...

class Generos(_message.Message):
    __slots__ = ("generos",)
    GENEROS_FIELD_NUMBER: _ClassVar[int]
    generos: _containers.RepeatedCompositeFieldContainer[Genero]
    def __init__(self, generos: _Optional[_Iterable[_Union[Genero, _Mapping]]] = ...) -> None: ...

class Artistas(_message.Message):
    __slots__ = ("artistas",)
    ARTISTAS_FIELD_NUMBER: _ClassVar[int]
    artistas: _containers.RepeatedCompositeFieldContainer[Artista]
    def __init__(self, artistas: _Optional[_Iterable[_Union[Artista, _Mapping]]] = ...) -> None: ...

class Albuns(_message.Message):
    __slots__ = ("albuns",)
    ALBUNS_FIELD_NUMBER: _ClassVar[int]
    albuns: _containers.RepeatedCompositeFieldContainer[Album]
    def __init__(self, albuns: _Optional[_Iterable[_Union[Album, _Mapping]]] = ...) -> None: ...

class NovoUsuario(_message.Message):
    __slots__ = ("nome", "idade")
    NOME_FIELD_NUMBER: _ClassVar[int]
    IDADE_FIELD_NUMBER: _ClassVar[int]
    nome: str
    idade: int
    def __init__(self, nome: _Optional[str] = ..., idade: _Optional[int] = ...) -> None: ...

class NovaMusica(_message.Message):
    __slots__ = ("nome", "duracao_seg", "album_id", "genero_id")
    NOME_FIELD_NUMBER: _ClassVar[int]
    DURACAO_SEG_FIELD_NUMBER: _ClassVar[int]
    ALBUM_ID_FIELD_NUMBER: _ClassVar[int]
    GENERO_ID_FIELD_NUMBER: _ClassVar[int]
    nome: str
    duracao_seg: int
    album_id: int
    genero_id: int
    def __init__(self, nome: _Optional[str] = ..., duracao_seg: _Optional[int] = ..., album_id: _Optional[int] = ..., genero_id: _Optional[int] = ...) -> None: ...

class NovaPlaylist(_message.Message):
    __slots__ = ("nome", "usuario_id", "musicas")
    NOME_FIELD_NUMBER: _ClassVar[int]
    USUARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MUSICAS_FIELD_NUMBER: _ClassVar[int]
    nome: str
    usuario_id: int
    musicas: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, nome: _Optional[str] = ..., usuario_id: _Optional[int] = ..., musicas: _Optional[_Iterable[int]] = ...) -> None: ...

class AtualizaUsuario(_message.Message):
    __slots__ = ("id", "nome", "idade")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    IDADE_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    idade: int
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ..., idade: _Optional[int] = ...) -> None: ...

class AtualizaMusica(_message.Message):
    __slots__ = ("id", "nome", "duracao_seg", "album_id", "genero_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    DURACAO_SEG_FIELD_NUMBER: _ClassVar[int]
    ALBUM_ID_FIELD_NUMBER: _ClassVar[int]
    GENERO_ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    duracao_seg: int
    album_id: int
    genero_id: int
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ..., duracao_seg: _Optional[int] = ..., album_id: _Optional[int] = ..., genero_id: _Optional[int] = ...) -> None: ...

class AtualizaPlaylist(_message.Message):
    __slots__ = ("id", "nome", "musicas", "trocar_musicas")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    MUSICAS_FIELD_NUMBER: _ClassVar[int]
    TROCAR_MUSICAS_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    musicas: _containers.RepeatedScalarFieldContainer[int]
    trocar_musicas: bool
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ..., musicas: _Optional[_Iterable[int]] = ..., trocar_musicas: _Optional[bool] = ...) -> None: ...
