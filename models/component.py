
from models.base_model import BaseModel


class Component(BaseModel):
    def __init__(self, name, brand, type_name, size, grade, stats=None):
        self.name = name.upper()
        self.brand = brand.upper()
        self.type_name = type_name.upper() # Ex: SHIELD, QUANTUM_DRIVE
        self.size = size
        self.grade = grade
        self.stats = stats or {} # Dictionnaire pour les stats spécifiques (vitesse, regen, etc.)

    @classmethod
    def from_db(cls, row):
        """Transforme une ligne SQL en objet Component"""
        if not row: return None
        # Selon l'ordre de tes colonnes SQL : id, name, brand, type_name, size, grade, stats
        return cls(name=row[1], brand=row[2], type_name=row[3], size=row[4], grade=row[5], stats=row[6])