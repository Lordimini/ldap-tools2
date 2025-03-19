# flask_app/domain/models/paged_result.py
from typing import Dict, Any, Optional, TypeVar, Generic, List
from dataclasses import dataclass
from .result import Result

T = TypeVar('T')

@dataclass
class PagedResult(Generic[T]):
    """
    Modèle représentant un résultat paginé, utilisé pour les listes d'éléments.
    """
    items: List[T]
    total: int
    page: int
    page_size: int
    
    @property
    def total_pages(self) -> int:
        """
        Calcule le nombre total de pages.
        
        Returns:
            Nombre total de pages
        """
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_previous(self) -> bool:
        """
        Vérifie s'il y a une page précédente.
        
        Returns:
            True s'il y a une page précédente, False sinon
        """
        return self.page > 1
    
    @property
    def has_next(self) -> bool:
        """
        Vérifie s'il y a une page suivante.
        
        Returns:
            True s'il y a une page suivante, False sinon
        """
        return self.page < self.total_pages
    
    @property
    def previous_page(self) -> int:
        """
        Retourne le numéro de la page précédente.
        
        Returns:
            Numéro de la page précédente
        """
        return max(1, self.page - 1)
    
    @property
    def next_page(self) -> int:
        """
        Retourne le numéro de la page suivante.
        
        Returns:
            Numéro de la page suivante
        """
        return min(self.total_pages, self.page + 1)
    
    @classmethod
    def from_list(cls, items: List[T], page: int = 1, page_size: int = 20, total: Optional[int] = None) -> 'PagedResult[T]':
        """
        Crée un résultat paginé à partir d'une liste d'éléments.
        
        Args:
            items: Liste complète d'éléments
            page: Numéro de page actuel
            page_size: Taille de la page
            total: Nombre total d'éléments (par défaut la taille de la liste)
            
        Returns:
            Instance PagedResult
        """
        if total is None:
            total = len(items)
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        # Paginer les éléments
        paged_items = items[start_index:end_index]
        
        return cls(
            items=paged_items,
            total=total,
            page=page,
            page_size=page_size
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le résultat paginé en dictionnaire.
        
        Returns:
            Dictionnaire contenant les données du résultat paginé
        """
        items_data = []
        for item in self.items:
            if hasattr(item, 'to_dict'):
                items_data.append(item.to_dict())
            elif isinstance(item, dict):
                items_data.append(item)
            else:
                items_data.append(item)
        
        return {
            'items': items_data,
            'total': self.total,
            'page': self.page,
            'page_size': self.page_size,
            'total_pages': self.total_pages,
            'has_previous': self.has_previous,
            'has_next': self.has_next,
            'previous_page': self.previous_page,
            'next_page': self.next_page
        }
    
    def to_result(self) -> Result['PagedResult[T]']:
        """
        Convertit en Result pour une gestion d'erreur uniforme.
        
        Returns:
            Result encapsulant ce PagedResult
        """
        return Result.ok(self)