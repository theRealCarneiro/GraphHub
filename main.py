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
                "weight": str(edge.peso)
            })
        graphTimeLine.append({
            "id": grafo.id,
            "nome": grafo.nome_grafo,
            "nodes": nodes,
            "edges": edges,
            "edgesNumber": len(edges),
            "nodesNumber": len(nodes)
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
