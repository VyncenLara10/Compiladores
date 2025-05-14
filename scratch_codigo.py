from grafodirigdo import Grafodirigido
from node import Node



def main():

    nodo1 = Node(1, "Inicio")
    grafo = Grafodirigido(nodo1)

    nodo2 =  grafo.agregar_vertice(1, "i = 1")
    nodo3 =  grafo.agregar_vertice(1, "i == 2")
    nodo4 =  grafo.agregar_vertice(1, "si")
    nodo5 =  grafo.agregar_vertice(1, "no")
    nodo6 =  grafo.agregar_vertice(1, "error")
    nodo7 =  grafo.agregar_vertice(1, "final")



    grafo.agregar_arista(nodo1,nodo2)
    grafo.agregar_arista(nodo2, nodo3)
    grafo.agregar_arista(nodo3 ,nodo4)
    grafo.agregar_arista(nodo3 ,nodo5)
    grafo.agregar_arista(nodo4,nodo7)
    grafo.agregar_arista(nodo5,nodo6)

    print(grafo.mostrar())
    print(" ----- ")
    print(" ----- ")
    print(" ")
    grafo.eliminar(nodo5)
    print(grafo.mostrar())

main()