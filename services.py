import sqlalchemy.orm as _orm
import models as _models, schemas as _schemas, database as _database
#from models import User

def create_database():
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
 

def get_user(db: _orm.Session, user_id: int):
    return db.query(_models.User).filter(_models.User.id == user_id).first()

def get_user_by_username(db: _orm.Session, username: str):
    return db.query(_models.User).filter(_models.User.username == username).first()

def create_user(db: _orm.Session, user: _schemas.UserCreate):
    fake_hashed_password = user.password 
    db_user = _models.User(username=user.username, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_graph(db: _orm.Session, graph_id: int):
    return db.query(_models.Grafo).filter(_models.Grafo.id == graph_id).first()

def get_graph_by_name(db: _orm.Session, graph_name: str, user_id: int):
    db_graph = db.query(_models.Grafo).filter(_models.Grafo.user_id == user_id)
    if db_graph:
        for graph in db_graph:
            if graph.nome_grafo == graph_name:
                return True
    return None

def create_graph(db: _orm.Session, graph: _schemas.GraphCreate, user: _schemas.User):
    db_graph = _models.Grafo(nome_grafo=graph["nome_grafo"], user_id=user.id, NumerosDeNo=graph["numerosDeNo"], NumeroDeArestas=graph["numeroDeArestas"])
    db.add(db_graph)
    db.commit()
    db.refresh(db_graph)
    return db_graph


def get_node_by_name(db: _orm.Session, node_name: str, graph_id: int):
    return db.query(_models.No).filter(_models.No.nome_no == node_name and _models.No.grafo_id == graph_id).first()

def create_node(db: _orm.Session, node: _schemas.NodeCreate, graph: _schemas.Graph):
    db_node = _models.No(nome_no=node["nome_no"], grafo_id=graph.id)
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node


def get_edge(db: _orm.Session, edge_target: int, edge_source: int, edge_peso: int, graph_id: int):
    return db.query(_models.Aresta).filter(_models.Aresta.target_id == edge_target 
                                       and _models.Aresta.source_id == edge_source
                                       and _models.Aresta.peso == edge_peso
                                       and _models.Aresta.grafo_id == graph_id).first()

def create_edge(db: _orm.Session, edge: _schemas.EdgeCreate, graph: _schemas.Graph):
    db_edge = _models.Aresta(peso=edge["peso"], source_id=edge["source_id"], target_id=edge["target_id"], grafo_id=graph.id)
    db.add(db_edge)
    db.commit()
    db.refresh(db_edge)
    return db_edge


def get_nodes(db: _orm.Session, id_grafo: int):
    return db.query(_models.No).filter(_models.No.grafo_id  == id_grafo).all()

#SPRINT3: Pegar nó pelo id 
def get_node(db: _orm.Session, node_id: str):
    return db.query(_models.No).filter(_models.No.id == node_id).first()

def get_node_by_name(db: _orm.Session, node_name: str, graph_id: int):
    return db.query(_models.No).filter(_models.No.nome_no == node_name and _models.No.grafo_id == graph_id).first()

def create_node(db: _orm.Session, node: _schemas.NodeCreate, graph: _schemas.Graph):
    db_node = _models.No(nome_no=node["nome_no"], grafo_id=graph.id)
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node


