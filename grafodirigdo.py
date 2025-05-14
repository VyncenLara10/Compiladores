from node import Node

class Grafodirigido():
    def __init__(self, cabeza: Node):
        self.head = cabeza
        self.adyacencia = {}
        self.adyacencia[self.head] = []

    def agregar_vertice(self, tipo: int, informacion: str) -> Node:
        new_node = Node(tipo, informacion)
        if new_node not in self.adyacencia:
            self.adyacencia[new_node] = []
        return new_node  # Importante para usar luego en aristas

    def obtener_nodo_por_info(self, informacion: str) -> Node:
        for nodo in self.adyacencia:
            if nodo.informacion == informacion:
                return nodo
        return None  # Si no existe

    def agregar_arista(self, origen: Node, destino: Node):
        if origen in self.adyacencia and destino in self.adyacencia:
            self.adyacencia[origen].append(destino)
        else:
            raise ValueError("Uno o ambos nodos no existen en el grafo")

    def _caminos_grafo(self):
        txt = self.head.return_info()
        inicio = self.head
        next = self.adyacencia[inicio][0]
        return self.caminos_grafo(next, txt)

    def caminos_grafo(self, node: Node, text: str):
        text += " -> " + node.return_info()
        if len(self.adyacencia[node]) == 2:
            izquierda = self.adyacencia[node][0]
            derecha = self.adyacencia[node][1]
            self.caminos_grafo(izquierda, text)
            self.caminos_grafo(derecha, text)

        elif len(self.adyacencia[node]) == 1:
            next = self.adyacencia[node][0]
            text += " -> " + next.return_info()
            return  self.caminos_grafo(next, text)

    def mostrar(self):
        txt = ""
        for clave, lista_adyacente in self.adyacencia.items():
            txt += clave.return_info() + " -> "
            for adyacente in lista_adyacente:
                txt += adyacente.return_info() + " | "
            txt += "\n"
        return txt


    def eliminar(self, nodo: Node):
        if nodo in self.adyacencia:
            valor = self.adyacencia.pop(nodo)

        for clave, lista_adyacente in self.adyacencia.items():
            for adyacente in lista_adyacente:
                if adyacente == nodo:
                    lista_adyacente.remove(adyacente)


        return valor
