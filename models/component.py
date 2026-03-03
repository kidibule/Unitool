from models.base_model import BaseModel

class Component(BaseModel):
    def __init__(self, name, brand, type_name, category, size, grade, stats=None):
        self.name = (name or "UNKNOWN").upper()
        self.brand = (brand or "UNKNOWN").upper()
        self.type_name = (type_name or "UNKNOWN").upper()
        
        # Sécurité pour la catégorie
        self.category = (category or "SYSTEM").upper() 
        
        self.size = size
        self.grade = (grade or "C").upper()
        self.stats = stats or {}
        
    @classmethod
    def from_db(cls, row):
        """
        Transforme une ligne SQL en objet Component.
        Adapté pour l'ordre : id, name, brand, type_name, category, size, grade, stats
        """
        if not row: return None
        
        return cls(
            name=row[1], 
            brand=row[2], 
            type_name=row[3], 
            category=row[4], 
            size=row[5], 
            grade=row[6], 
            stats=row[7] if len(row) > 7 else {}
        )