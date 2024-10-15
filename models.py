from app import db, app
from flask import jsonify, current_app
import json
from sqlalchemy.orm import relationship, declarative_base, sessionmaker 
from sqlalchemy import Column, Integer, String, ForeignKey, Table

class HighScore(db.Model):
    __tablename__ = "highscore"
    id = db.Column(Integer, primary_key=True)
    score = db.Column(Integer, nullable=False)
    player_name = db.Column(String, nullable=False, unique=True)
    

