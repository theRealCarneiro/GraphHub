import sqlalchemy.orm as _orm
import models as _models, schemas as _schemas, database as _database
#from models import User
import fastapi as _fastapi


def create_database():
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
 


#operações com usuário

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


#operações com grafos
def get_graph(db: _orm.Session, graph_id: int):
    return db.query(_models.Grafo).filter(_models.Grafo.id == graph_id).first()

def get_graphs(db: _orm.Session, user_id: int):
    return db.query(_models.Grafo).filter(_models.Grafo.user_id == user_id).all()


def get_graph_by_name(db: _orm.Session, graph_name: str, user_id: int):
    db_graph = db.query(_models.Grafo).filter(_models.Grafo.user_id == user_id)
    if db_graph:
        for graph in db_graph:
            if graph.nome_grafo == graph_name:
                return True
    return None

def create_graph(db: _orm.Session, graph: _schemas.GraphCreate, user: _schemas.User):
    db_graph = _models.Grafo(nome_grafo=graph["nome_grafo"], user_id=user.id, publico=graph["publico"])
    db.add(db_graph)
    db.commit()
    db.refresh(db_graph)
    return db_graph

def edit_graph(db: _orm.Session, graph: _schemas.GraphCreate, nome_novo):
    graph.nome_grafo = nome_novo
    db.commit()
    db.refresh(graph)
    return graph

def edit_graph_visib(db: _orm.Session, graph: _schemas.GraphCreate, isPublic):
    
    if isPublic == True:
        graph.publico = False
    else:
        graph.publico = True
    
    db.commit()
    db.refresh(graph)
    return graph


def forkGraph(db, graph_id, user_id):
    user =  get_user(db, user_id)
    graph_aux = get_graph(db, graph_id)

    gc = {
        "nome_grafo": graph_aux.nome_grafo,
        "publico": True,
    }


    graph = create_graph(db, gc, user)
    
    nodes = get_nodes(db, graph_id)
    edges =  get_edges(db, graph_id)
    
    
    
    if graph and nodes and edges and user:
        
        for node in nodes:
            node_aux = {
                "nome_no": node.nome_no,
            }
            create_node(db, node_aux, graph)
        
        
        for edge in edges:
            target_aux = get_node(db, edge.target_id)
            source_aux = get_node(db, edge.source_id)

            target = get_node_by_name(db, target_aux.nome_no, graph.id)
            source = get_node_by_name(db, source_aux.nome_no, graph.id)
            
            edge_aux = {
                "target_id": target.id,
                "source_id": source.id,
                "peso": edge.peso
            }
            create_edge(db, edge_aux, graph)

       
        return True
    
    else:
        return False


    
def registerGraph(df, db, nome_arquivo, user_id, publico):
    db_graph = get_graph_by_name(db=db, graph_name=nome_arquivo, user_id=user_id)
    
    if db_graph:
        raise _fastapi.HTTPException(
            status_code= 406, detail=" Este Grafo possuí o mesmo nome que outro já cadastrado"
        )
    else:  
        user = get_user(db=db, user_id=user_id)
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
            "publico": publico,
            "isforked": False
        }

        grafo = create_graph(db=db, graph=graph, user=user) 

        for node in nodes_list:
            no = {
                    "nome_no": node,
                    "grafo_id": grafo.id
            }
            create_node(db=db, node=no, graph=grafo)
                
        for edge in edges_list:
                target = get_node_by_name(db=db, node_name=edge[1], graph_id=grafo.id)
                source = get_node_by_name(db=db, node_name=edge[0], graph_id=grafo.id)
                aresta = {
                    "target_id": target.id,
                    "source_id": source.id,
                    "peso": edge[2],
                    "grafo_id": grafo.id
                }
                create_edge(db=db, edge=aresta, graph=grafo)
        return True

def deletar_grafo(db: _orm.Session, grafo_id: int):
    db_graph = get_graph(db, grafo_id)
    db.delete(db_graph)
    db.commit()
#-------------------------------------------------

#operações com nós
def update_node(db: _orm.Session, node_id: int, nome_no: str):
    db_node = get_node(db=db, node_id=node_id)
    db_node.nome_no = nome_no
    db.commit()
    db.refresh(db_node)
    return db_node

def get_node_by_name(db: _orm.Session, node_name: str, graph_id: int):
        nodes = db.query(_models.No).filter((_models.No.grafo_id == graph_id)).all()
        for node in nodes:
            if node.nome_no == node_name:
                return  node
def create_node(db: _orm.Session, node: _schemas.NodeCreate, graph: _schemas.Graph):
    db_node = _models.No(nome_no=node["nome_no"], grafo_id=graph.id)
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node


def get_nodes(db: _orm.Session, id_grafo: int):
    return db.query(_models.No).filter(_models.No.grafo_id  == id_grafo).all()

def get_node(db: _orm.Session, node_id: str):
    return db.query(_models.No).filter(_models.No.id == node_id).first()

def deletar_nos(db: _orm.Session, grafo_id: int, grafo):
    list_nodes = get_nodes(db, id_grafo=grafo_id)
    for node in list_nodes:
        delete_node(db=db, node_id=node.id, grafo=grafo)

def delete_node(db: _orm.Session, node_id: int, grafo):
    db_node = get_node(db=db, node_id=node_id)
    db.delete(db_node)
    db.commit()
#-----------------------------------------------



#operações com arestas

def get_edge(db: _orm.Session, edge_id: int):
    return db.query(_models.Aresta).filter(_models.Aresta.id == edge_id ).first()
def get_edges(db: _orm.Session, grafo_id: int):
    return db.query(_models.Aresta).filter(_models.Aresta.grafo_id == grafo_id).all()

def create_edge(db: _orm.Session, edge: _schemas.EdgeCreate, graph: _schemas.Graph):
    db_edge = _models.Aresta(peso=edge["peso"], source_id=edge["source_id"], target_id=edge["target_id"], grafo_id=graph.id)
    db.add(db_edge)
    db.commit()
    db.refresh(db_edge)
    return db_edge

def deletar_arestas(db: _orm.Session, grafo_id: int, grafo):
    list_arestas = get_edges(db, grafo_id=grafo_id)
    for aresta in list_arestas:
        delete_edge(db, edge_id=aresta.id, grafo=grafo)

def delete_edge(db: _orm.Session, edge_id: int, grafo):
    db_edge = get_edge(db,edge_id)
    db.delete(db_edge)
    db.commit()

def get_new_edge(db: _orm.Session, edge_target: int, edge_source: int, edge_peso: int, graph_id: int):
    return db.query(_models.Aresta).filter(_models.Aresta.target_id == edge_target 
                                       and _models.Aresta.source_id == edge_source
                                       and _models.Aresta.peso == edge_peso
                                       and _models.Aresta.grafo_id == graph_id).first()

def update_edge(db: _orm.Session, edge_id: int, peso: str):
    db_edge = get_edge(db=db, edge_id=edge_id)
    db_edge.peso = peso
    db.add(db_edge)
    db.commit()
    db.refresh(db_edge)
    return db_edge


def get_edges_by_node(db: _orm.Session, node_id):
    return db.query(_models.Aresta).filter(_models.Aresta.target_id == node_id or _models.Aresta.source_id == node_id).all()



def search(db: _orm.Session, key):
    list_user = db.query(_models.User).filter().all()

    filteredUsers = []
    
    for user in list_user:
        count_public_repository = 0
        if (user.username.lower().startswith(key.lower())):
            graphs = db.query(_models.Grafo).filter(_models.Grafo.user_id == user.id).all()
            graphsFiltred = []
            for graph in graphs:
                if graph.publico == True:
                    count_public_repository+=1
                    

            aux = {"username": user.username,
                    "user_id": user.id,
                    "repositoriesNumber": count_public_repository}
            filteredUsers.append(aux)

    filteredUsers.sort(key=lambda d: (d['repositoriesNumber']*-1)) 
    return {"filteredUsers": filteredUsers}


def search_graph(db: _orm.Session, user_id):
    graphs = get_graphs(db, user_id)
    graphs_filtred = []
    for graph in graphs:
        if graph.publico == True:
            graphs_filtred.append(graph)
    
    return graphs_filtred