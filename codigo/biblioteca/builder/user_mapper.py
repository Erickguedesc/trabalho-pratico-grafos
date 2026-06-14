# =============================================================================
# user_mapper.py
# -----------------------------------------------------------------------------
# Responsabilidade:
#   Converter logins do GitHub (strings como "torvalds") em índices inteiros
#   (0, 1, 2, ...) para que o grafo possa trabalhar com eles.
#
# Por que isso é necessário?
#   A nossa implementação de grafo (AdjacencyMatrixGraph e AdjacencyListGraph)
#   usa índices inteiros para identificar vértices. Mas os dados que vêm do
#   GitHub usam logins de texto. Este arquivo faz a ponte entre os dois mundos.
#
# Exemplo:
#   login "alice"  ->  índice 0
#   login "bob"    ->  índice 1
#   login "carol"  ->  índice 2
#   índice 0       ->  login "alice"  (consulta inversa)
# =============================================================================


class UserMapper:
    """
    Mapeia logins do GitHub para índices inteiros e vice-versa.

    Funciona como um dicionário bidirecional:
      - login_to_id:  login (str) -> índice (int)
      - id_to_login:  índice (int) -> login (str)

    O UserMapper é construído antes do grafo, pois precisamos saber
    quantos usuários únicos existem para definir o tamanho (num_vertices)
    dos grafos que serão criados.
    """

    def __init__(self):
        """
        Cria um UserMapper vazio.

        Os dois dicionários começam vazios e são preenchidos conforme
        logins são adicionados via add_login().
        """

        # Dicionário principal: login -> índice inteiro.
        # Exemplo: {"alice": 0, "bob": 1}
        self._login_to_id: dict[str, int] = {}

        # Dicionário inverso: índice inteiro -> login.
        # Exemplo: {0: "alice", 1: "bob"}
        self._id_to_login: dict[int, str] = {}

    def add_login(self, login: str) -> int:
        """
        Registra um login no mapper e retorna seu índice.

        Se o login já foi registrado antes, apenas retorna o índice existente
        sem criar duplicata. Se for novo, atribui o próximo índice disponível.

        Recebe:
            login (str): login do GitHub do usuário.

        Retorna:
            int: índice inteiro atribuído ao login.

        Exemplo:
            mapper.add_login("alice")  ->  0  (primeiro a entrar)
            mapper.add_login("bob")    ->  1  (segundo a entrar)
            mapper.add_login("alice")  ->  0  (já existia, retorna o mesmo)
        """

        # Se o login já foi registrado, retorna o índice já existente.
        if login in self._login_to_id:
            return self._login_to_id[login]

        # O novo índice será o tamanho atual do dicionário.
        # Como começa em 0, o primeiro login recebe 0, o segundo recebe 1, etc.
        new_id = len(self._login_to_id)

        # Registra nos dois dicionários para permitir consulta nos dois sentidos.
        self._login_to_id[login] = new_id
        self._id_to_login[new_id] = login

        return new_id

    def get_id(self, login: str) -> int:
        """
        Retorna o índice inteiro de um login já registrado.

        Recebe:
            login (str): login do GitHub.

        Retorna:
            int: índice atribuído ao login.

        Lança:
            KeyError: se o login não foi registrado anteriormente.

        Uso:
            Chamado pelo GraphBuilder ao adicionar arestas, para converter
            source_user e target_user em índices u e v.
        """

        if login not in self._login_to_id:
            raise KeyError(f"Login não registrado no mapper: '{login}'")

        return self._login_to_id[login]

    def get_login(self, user_id: int) -> str:
        """
        Retorna o login de um índice já registrado (consulta inversa).

        Recebe:
            user_id (int): índice inteiro do vértice.

        Retorna:
            str: login do GitHub associado ao índice.

        Lança:
            KeyError: se o índice não existe no mapper.

        Uso:
            Chamado pelo GraphAnalyzer e pelo DemoCLI para exibir resultados
            com o nome do usuário em vez do número do vértice.
        """

        if user_id not in self._id_to_login:
            raise KeyError(f"ID não registrado no mapper: {user_id}")

        return self._id_to_login[user_id]

    def num_users(self) -> int:
        """
        Retorna a quantidade total de usuários registrados.

        Retorna:
            int: número de logins únicos registrados até agora.

        Uso:
            Chamado pelo GraphBuilder para criar os grafos com o tamanho certo:
                graph = AdjacencyListGraph(mapper.num_users())
        """

        return len(self._login_to_id)

    def all_logins(self) -> list[str]:
        """
        Retorna a lista de todos os logins registrados, em ordem de inserção.

        Retorna:
            list[str]: lista de logins, onde a posição i é o login com índice i.

        Exemplo:
            Se foram registrados "alice" (0), "bob" (1), "carol" (2):
            Retorna: ["alice", "bob", "carol"]

        Uso:
            Útil para inicializar os rótulos dos vértices nos grafos.
        """

        # Como os índices vão de 0 até num_users-1, pode-se ordenar pelo índice.
        return [self._id_to_login[i] for i in range(len(self._id_to_login))]

    def __repr__(self) -> str:
        """
        Representação textual do mapper, útil para debug.

        Exibe os primeiros 5 mapeamentos registrados.
        """

        preview = list(self._login_to_id.items())[:5]
        return f"UserMapper({len(self._login_to_id)} usuários | primeiros: {preview})"