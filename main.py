from typing import List
import fastapi as _fastapi
import sqlalchemy.orm as _orm
import services as _services, schemas as _schemas
from fastapi.middleware.cors import CORSMiddleware
from fastapi import  File, UploadFile, Form
import io
import pandas as pd
import numpy as np
import math


## uvicorn main:app --reload
## http://127.0.0.1:8000
## http://127.0.0.1:8000/docs#/

app = _fastapi.FastAPI()
_services.create_database()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def receberArquivo(file_read):  
    return df

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


def cadastroGrafoCompleto(df, db, nome_arquivo, user_id):
    db_graph = _services.get_graph_by_name(db=db, graph_name=nome_arquivo, user_id=user_id)
    
    if db_graph:
        raise _fastapi.HTTPException(
            status_code= 406, detail=" Este Grafo possuí o mesmo nome que outro já cadastrado"
        )
    else:  
        user = _services.get_user(db=db, user_id=user_id)
        

        
        nodes_list = []
        edges_list = []
        df = df.reset_index()

        for index, row in df.iterrows():
            if row[0] not in nodes_list:
                nodes_list.append(row[0])
            if row[1] not in nodes_list:
                nodes_list.append(row[1])

            arestas = (row[0], row[1], row[2])
            if arestas not in edges_list:
                edges_list.append(arestas)
        

        graph = {
            "nome_grafo": nome_arquivo,
            "numerosDeNo": len(nodes_list),
            "numeroDeArestas": len(edges_list),
            "user_id": user.id 
        }

        grafo = _services.create_graph(db=db, graph=graph, user=user) 

        for node in nodes_list:  
                no = {
                    "nome_no": node,
                    "grafo_id": grafo.id
                }
                _services.create_node (db=db, node=no, graph=grafo)
                
        for edge in edges_list:  
            db_edge = _services.get_edge(db=db, edge_target=edge[1], edge_source=edge[0], edge_peso=edge[2], graph_id=grafo.id)   
            if (db_edge is None):  
                aresta = {
                    "target_id": edge[1],
                    "source_id": edge[0],
                    "peso": edge[2],
                    "grafo_id": grafo.id
                }
                _services.create_edge (db=db, edge=aresta, graph=grafo)
        return True



@app.post("/cadastro/grafo/")
async def create_graph(file: UploadFile, user_id: int = Form(...), db: _orm.Session = _fastapi.Depends(_services.get_db)):
    file_read = await file.read()
    nome_arquivo = file.filename
    texto = file_read.decode("utf-8")
    buffer = io.StringIO(texto)
    df = pd.read_csv(filepath_or_buffer = buffer, header=None)


    check_nan_in_df = df.isnull().values.any()


    if (check_nan_in_df):
        raise _fastapi.HTTPException(
            status_code=406, detail="Ha linhas nulas em seu txt corrija para realizar o cadastro"
            )
    if (df.iloc[:, 2].dtypes <= np.integer):
          status_code=200
          if(cadastroGrafoCompleto(df, db, nome_arquivo, user_id)):
              raise _fastapi.HTTPException(
            status_code=200, detail="Grafo cadastrado com sucesso!"
            ) 
    else:
          raise _fastapi.HTTPException(
            status_code=406, detail=" Em sua coluna de pesos ha valores que nao são inteiros corrija para realizar o cadastro"
            ) 


    


# @app.get("/users/", response_model=List[_schemas.User])
# def read_users(
#         skip: int = 0,
#         limit: int = 10,
#         db: _orm.Session = _fastapi.Depends(_services.get_db),
#     ):
#     users = _services.get_users(db=db, skip=skip, limit=limit)
#     return users
