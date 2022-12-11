from typing import List
import fastapi as _fastapi
import sqlalchemy.orm as _orm
import services as _services, schemas as _schemas
from fastapi.middleware.cors import CORSMiddleware
from fastapi import  File, UploadFile, Form
import io
import pandas as pd
import numpy as np
from starlette.requests import Request
from operator import itemgetter
from fastapi.responses import FileResponse



## uvicorn main:app --reload
## http://127.0.0.1:8000
## http://127.0.0.1:8000/docs#/

app = _fastapi.FastAPI()
_services.create_database()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/users/{user_username}/{user_password}")
def read_user(
    user_username: str, user_password: str, db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    db_user = _services.get_user_by_username(db=db, username=user_username)
    
    if db_user is None:
        raise _fastapi.HTTPException(
            status_code=401, detail= "Não possui uma conta nesse nome de usuário."
        )
        
    else:
        if (user_password == db_user.hashed_password):
                        return {"username": user_username,
                    "user_id": db_user.id}
        else:
            raise _fastapi.HTTPException(
                status_code=403, detail= "A senha está errada."
            )
                      

@app.post("/users/", response_model=_schemas.User, status_code=200)
async def create_user(
    user: _schemas.UserCreate, db: _orm.Session = _fastapi.Depends(_services.get_db)
):
    db_user = _services.get_user_by_username(db=db, username=user.username)
    if db_user:
        raise _fastapi.HTTPException(
            status_code= 409, detail="Esse nome de usuario ja esta em uso"
        )
    return _services.create_user(db=db, user=user)


@app.post("/cadastro/grafo_vazio")
async def create_graph_empty(request: Request, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    request = await request.json()
    user_id = request["user_id"]
    publico = request["publico"]
    nome_grafo = request["nome_grafo"]
    #busca usuário no banco
    # request
    user = _services.get_user(db, user_id)
    #caso o usuário exista, cria o grafo e o adiciona no banco
    if user:
        graph = {
            "nome_grafo": nome_grafo,
            "publico": publico,
            "user_id": user_id,
            "isforked": False
        }
        _services.create_graph(db=db, graph=graph, user=user)
        return "Grafo cadastrado com sucesso!"
    #caso usuário não exista, sobe uma exceção
    else:
        raise _fastapi.HTTPException(
            status_code=401, detail="Não existe usuário com este ID"
        )


        
@app.post("/cadastro/grafo/")
async def create_graph(file: UploadFile, user_id: int = Form(...), publico: bool = Form(...), db: _orm.Session = _fastapi.Depends(_services.get_db)):
    file_read = await file.read()
    nome_arquivo = file.filename.split(".")
    texto = file_read.decode("utf-8")
    buffer = io.StringIO(texto)
    df = pd.read_csv(filepath_or_buffer = buffer, header=None)


    check_nan_in_df = df.isnull().values.any()


    if (check_nan_in_df):
        raise _fastapi.HTTPException(
            status_code=406, detail="Ha linhas nulas em seu txt corrija para realizar o cadastro"
            )
    if (df.iloc[:, 2].dtypes <= np.integer):
          if(_services.registerGraph(df, db, nome_arquivo[0], user_id, publico)):
                return "Grafo cadastrado com sucesso!"
    else:
          raise _fastapi.HTTPException(
            status_code=406, detail=" Em sua coluna de pesos ha valores que nao são inteiros corrija para realizar o cadastro"
            )


@app.get("/lista/grafos/{user_id}")
async def lista_grafo(user_id: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    graphTimeLine = []

    grafos = _services.get_graphs(db=db, user_id=user_id)
    for grafo in grafos:
        nodes = []
        edges = []
        list_nodes = _services.get_nodes(db=db, id_grafo=grafo.id)
        list_edges = _services.get_edges(db=db, grafo_id=grafo.id)
        for node in list_nodes:
            nodes.append({
                "id": node.id,
                "label": node.nome_no,
            })
        for edge in list_edges:
            edges.append({
                "from": edge.source_id,
                "to": edge.target_id,
                "label": str(edge.peso)
            })
        graphTimeLine.append({
            "id": grafo.id,
            "nome": grafo.nome_grafo,
            "nodes": nodes,
            "edges": edges,
            "edgesNumber": len(edges),
            "nodesNumber": len(nodes),
            "isPublic": grafo.publico
        })
    return {"graphTimeLine": graphTimeLine}


@app.get("/excluir/grafo/{id_grafo}")
async def excluir_grafo(id_grafo: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    grafo = _services.get_graph(db, id_grafo)
    if grafo:
        _services.deletar_arestas(db, id_grafo, grafo=grafo)
        _services.deletar_nos(db, id_grafo, grafo)
        _services.deletar_grafo(db, id_grafo)
        return "Grafo excluido com sucesso"

    raise _fastapi.HTTPException(
        status_code=404, detail="Grafo inexistente!"
    )

@app.post("/edita/grafo/")
async def edit_graph(request: Request, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    request = await request.json()
    id_grafo = request["id_grafo"]
    nome_grafo = request["nome_grafo"]
    grafo = _services.get_graph(db, id_grafo)
    if grafo:
            if _services.edit_graph(db, grafo, nome_grafo):
                return "Grafo editado com sucesso"
            else:
                raise _fastapi.HTTPException(
                    status_code=400, detail="Não foi possível editar o grafo!"
                )

    else:
        raise _fastapi.HTTPException(
            status_code=404, detail="Grafo inexistente!"
        )

@app.get("/edita/grafo/visibility/{id_grafo}")
async def edit_graph_visibility(id_grafo: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    graph = _services.get_graph(db, id_grafo)
    if graph:
            if _services.edit_graph_visib(db, graph, graph.publico):
                return "Visibilidade do grafo editada com sucesso"
            else:
                raise _fastapi.HTTPException(
                    status_code=400, detail="Não foi possível editar a visibilidade do grafo!"
                )

    else:
        raise _fastapi.HTTPException(
            status_code=404, detail="Grafo inexistente!"
        )
# ----------------------------------------------------------------------------------------------------------


# OPERAÇÕES COM NÓS ---------------------------------------------------------------------------------------------------------------------    
@app.get("/criar/no/{nome_no}/{graph_id}")
#async def create_node(node: _schemas.NodeCreate, graph_id: int = Form(...), db: _orm.Session = _fastapi.Depends(_services.get_db)):
async def create_node(nome_no: str, graph_id: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
      
    grafo = _services.get_graph(db=db, graph_id=graph_id)
    if (grafo is None): #OU if(grafo is None) ????
        raise _fastapi.HTTPException(
            status_code= 404, detail="Grafo não encontrado"
        )       
    
    db_node = _services.get_node_by_name(db=db, node_name=nome_no, graph_id=grafo.id)   
    if (db_node is None):  
        no = {
            "nome_no": nome_no,
            "grafo_id": grafo.id
        }
        _services.create_node (db=db, node=no, graph=grafo);
        raise _fastapi.HTTPException(
            status_code= 200, detail="Nó criado com sucesso!"
        )
            
                      
#SPRINT3: Deletar nó
@app.get("/deletar/no/{node_id}")
async def delete_node(node_id: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    
    node = _services.get_node(db=db, node_id=node_id)
    if (node is None):
        raise _fastapi.HTTPException(
            status_code= 404, detail="Nó não encontrado. Id passado não corresponde a nenhum nó salvo"
        )
    else:

        grafo = _services.get_graph(db, node.grafo_id)
        _services.delete_node(db=db, node_id=node_id, grafo=grafo)
        list_edges_with_node = _services.get_edges_by_node(db, node_id=node_id)
        for edge in list_edges_with_node:
            _services.delete_edge(db, edge_id=edge.id, grafo=grafo)
        
        raise _fastapi.HTTPException(
            status_code= 200, detail="Nó delatado com sucesso!"
        )
        
#SPRINT3: Editar nó
@app.get("/editar/no/{node_id}/{nome_no}")
async def update_node(nome_no: str, node_id: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    
    node = _services.get_node(db=db, node_id=node_id)
    if (node is None):
        raise _fastapi.HTTPException(
            status_code= 404, detail="Nó não encontrado. Id passado não corresponde a nenhum nó salvo"
        )
    else:
        _services.update_node (db=db, node_id=node_id, nome_no=nome_no)
        raise _fastapi.HTTPException(
            status_code= 200, detail="Nó editado com sucesso!"
        )


@app.get("/lista/nos/{id_grafo}")
async def lista_grafo(id_grafo: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    list_nodes = _services.get_nodes(db=db, id_grafo=id_grafo)
    nodes_list = []
    for node in list_nodes:
        nodes_list.append({
            "id": node.id,
            "label": node.nome_no
        })
    return nodes_list

# -------------------------------------------------------------------------------------------------------


# OPERAÇÕES COM ARESTAS -------------------------------------------------------------------------------------------------------------------------
# Criar aresta
@app.get("/criar/aresta/{no1_id}/{no2_id}/{peso}/{graph_id}")
async def create_edge(no1_id: int,no2_id:int,peso:str, graph_id: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
      
    grafo = _services.get_graph(db=db, graph_id=graph_id)
    if (grafo is None):
        raise _fastapi.HTTPException(
            status_code= 404, detail="Grafo não encontrado"
        )        

    db_edges = _services.get_edges(db=db, grafo_id=grafo.id)
    for edge in db_edges:
        if edge.source_id == no2_id and edge.target_id == no1_id:
            raise _fastapi.HTTPException(
            status_code= 404, detail="Aresta já existe!"
        )   
    
 
    aresta = {
        "target_id": no1_id,
        "source_id": no2_id,
        "peso": peso,
        "grafo_id": grafo.id
        }
    return _services.create_edge(db=db, edge=aresta, graph=grafo)
    
     
                      
#Deletar aresta
@app.get("/deletar/aresta/{edge_id}")
async def delete_edge(edge_id: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    
    edge = _services.get_edge(db=db, edge_id=edge_id)
    if (edge is None):
        raise _fastapi.HTTPException(
            status_code= 404, detail="Aresta não encontrada."
        )
    else:
        grafo = _services.get_graph(db, edge.grafo_id)
        _services.delete_edge(db=db, edge_id=edge_id, grafo=grafo)
       
     
        
# Editar aresta
@app.get("/editar/aresta/{edge_id}/{peso}")
async def update_edge(peso: str, edge_id: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    
    edge = _services.get_edge(db=db, edge_id=edge_id)
    if (edge is None):
        raise _fastapi.HTTPException(
            status_code= 404, detail="Aresta não encontrada."
        )
    else:
        _services.update_edge (db=db, edge_id=edge_id, peso=peso)



# Listar Arestas
@app.get("/lista/aresta/{id_grafo}")
async def lista_aresta(id_grafo: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    try:
        edge_list = []
        list_edges = _services.get_edges(db=db, grafo_id=id_grafo)
        for edge in list_edges:
            source = _services.get_node(db, edge.source_id)
            target = _services.get_node(db, edge.target_id)
            edge_list.append({
                "id": edge.id,
                "Source": source.nome_no,
                "Target": target.nome_no,
                "Source_id": source.id,
                "Target_id":  target.id,
                "peso": str(edge.peso)
            })
        return edge_list
    except:
        edge_list = []
        return edge_list



@app.get("/pesquisa/{key}")
async def search(key, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    filteredUsers = _services.search(db, key)
    return filteredUsers


@app.get("/pesquisa/listagem/{username}")
async def graphslisted(username: str, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    
    user = _services.get_user_by_username(db, username)
    if user:
        graph_list = _services.search_graph(db,user.id)
        graphTimeLine = []
        for graph in graph_list:
            nodes = []
            edges = []
            list_nodes = _services.get_nodes(db=db, id_grafo=graph.id)
            list_edges = _services.get_edges(db=db, grafo_id=graph.id)
            for node in list_nodes:
                nodes.append({
                    "id": node.id,
                    "label": node.nome_no,
                })
            for edge in list_edges:
                edges.append({
                    "from": edge.source_id,
                    "to": edge.target_id,
                    "label": str(edge.peso)
                })
            graphTimeLine.append({
                "id": graph.id,
                "nome": graph.nome_grafo,
                "nodes": nodes,
                "edges": edges,
                "edgesNumber": len(edges),
                "nodesNumber": len(nodes)
            })
        return {"graphTimeLine": graphTimeLine}
    else:
        raise _fastapi.HTTPException(
            status_code= 400, detail="Usuário não encontrado!"
        )
        

@app.get("/download/{graph_id}")
async def download_graph(graph_id: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    
    graph =  _services.get_graph(db, graph_id)
    if graph:
        edges_list = _services.get_edges(db, graph_id)
        arq = open("./" + graph.nome_grafo, "w")
        i = 0
        if arq:
            for edge in edges_list:
                node_source = _services.get_node(db, edge.source_id)
                node_target = _services.get_node(db, edge.target_id)
                i+=1
                if i != len(edges_list):
                    arq.write(node_source.nome_no + "," + node_target.nome_no + "," + str(edge.peso)+"\n")
                else:
                    arq.write(node_source.nome_no + "," + node_target.nome_no + "," + str(edge.peso))
                
            return FileResponse("./" + graph.nome_grafo)
        else:
              raise _fastapi.HTTPException(
            status_code= 400, detail="Erro com o arquivo txt"
        )
    else:
       raise _fastapi.HTTPException(
            status_code= 404, detail="Grafo não encontrado."
        )


@app.get("/fork/{id_grafo}/{id_usuario}")
async def fork(id_grafo: int, id_usuario: int, db: _orm.Session = _fastapi.Depends(_services.get_db)):
    if _services.forkGraph(db, id_grafo, id_usuario):
        return "Grafo forkado com sucesso!"
    else:
        return "Erro ao forkar grafo!"