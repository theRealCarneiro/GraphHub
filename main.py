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
async def create_graph_empty(user_id: int = Form(...), publico: bool = Form(...), nome_grafo: str = Form(...), db: _orm.Session = _fastapi.Depends(_services.get_db)):
    #busca usuário no banco
    user = _services.get_user(db, user_id)
    #caso o usuário exista, cria o grafo e o adiciona no banco
    if user:
        graph = {
            "nome_grafo": nome_grafo,
            "publico": publico,
            "user_id": user_id
        }
        _services.create_graph(db=db, graph=graph, user=user)
        raise _fastapi.HTTPException(
            status_code=200, detail="Grafo cadastro com sucesso"
        )
    #caso usuário não exista, sobe uma exceção
    else:
        raise _fastapi.HTTPException(
            status_code=401, detail="Não existe usuário com este ID"
        )
        
@app.post("/cadastro/grafo/")
async def create_graph(file: UploadFile, user_id: int = Form(...), publico: bool = Form(...), db: _orm.Session = _fastapi.Depends(_services.get_db)):
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
          if(_services.registerGraph(df, db, nome_arquivo, user_id, publico)):
              raise _fastapi.HTTPException(
            status_code=200, detail="Grafo cadastrado com sucesso!"
            ) 
    else:
          raise _fastapi.HTTPException(
            status_code=406, detail=" Em sua coluna de pesos ha valores que nao são inteiros corrija para realizar o cadastro"
            ) 