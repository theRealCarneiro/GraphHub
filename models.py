from email.policy import default
from operator import index
import datetime as dt
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import database as _database

class User(_database.Base):
    __tablename__ = "usuario"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    username = _sql.Column(_sql.String, default=True)
    hashed_password = _sql.Column(_sql.String)


 
class Grafo(_database.Base):
    __tablename__ = "grafo"
    id = _sql.Column(_sql.Integer, primary_key =True, index=True)
    nome_grafo = _sql.Column(_sql.String, index=True)
    user_id = _sql.Column(_sql.Integer, _sql.ForeignKey("usuario.id"))



    publico = _sql.Column(_sql.Boolean, default=True)


class No(_database.Base):
    __tablename__ = "no"
    id = _sql.Column(_sql.Integer, primary_key =True, index=True)
    grafo_id = _sql.Column(_sql.Integer, _sql.ForeignKey("grafo.id"))
    nome_no = _sql.Column(_sql.String, index=True)

class Aresta(_database.Base):
    __tablename__ = "aresta"
    id = _sql.Column(_sql.Integer, primary_key =True, index=True)
    source_id = _sql.Column(_sql.Integer, _sql.ForeignKey("no.id"))
    target_id = _sql.Column(_sql.Integer, _sql.ForeignKey("no.id"))
    peso = _sql.Column(_sql.Integer, index=True)
    grafo_id = _sql.Column(_sql.Integer, _sql.ForeignKey("grafo.id")) 