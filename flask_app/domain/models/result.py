# flask_app/domain/models/result.py
from typing import Dict, Any, Optional, TypeVar, Generic, List, Union
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    """
    Modèle représentant le résultat d'une opération, que ce soit un succès ou un échec.
    Permet une approche fonctionnelle pour la gestion des erreurs.
    """
    success: bool
    value: Optional[T] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    @classmethod
    def ok(cls, value: T = None, details: Dict[str, Any] = None) -> 'Result[T]':
        """
        Crée un résultat réussi.
        
        Args:
            value: Valeur de retour
            details: Détails supplémentaires
            
        Returns:
            Instance Result indiquant un succès
        """
        return cls(success=True, value=value, details=details)
    
    @classmethod
    def fail(cls, error: str, details: Dict[str, Any] = None) -> 'Result[T]':
        """
        Crée un résultat d'échec.
        
        Args:
            error: Message d'erreur
            details: Détails supplémentaires sur l'erreur
            
        Returns:
            Instance Result indiquant un échec
        """
        return cls(success=False, error=error, details=details)
    
    def __bool__(self) -> bool:
        """
        Permet d'utiliser l'instance dans une condition booléenne.
        
        Returns:
            True si succès, False sinon
        """
        return self.success
    
    def unwrap(self) -> T:
        """
        Récupère la valeur en cas de succès, lance une exception sinon.
        
        Returns:
            Valeur de retour
            
        Raises:
            ValueError: Si le résultat est un échec
        """
        if not self.success:
            raise ValueError(f"Attempted to unwrap a failed Result: {self.error}")
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        """
        Récupère la valeur en cas de succès, ou la valeur par défaut sinon.
        
        Args:
            default: Valeur par défaut à retourner en cas d'échec
            
        Returns:
            Valeur de retour ou valeur par défaut
        """
        if not self.success:
            return default
        return self.value
    
    def map(self, f):
        """
        Applique une fonction à la valeur en cas de succès.
        
        Args:
            f: Fonction à appliquer
            
        Returns:
            Nouveau Result avec la valeur transformée, ou l'échec original
        """
        if not self.success:
            return self
        
        try:
            new_value = f(self.value)
            return Result.ok(new_value, self.details)
        except Exception as e:
            return Result.fail(str(e))
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le résultat en dictionnaire.
        
        Returns:
            Dictionnaire contenant les données du résultat
        """
        result = {'success': self.success}
        
        if self.success and self.value is not None:
            # Si la valeur est un dictionnaire ou a une méthode to_dict, l'utiliser
            if hasattr(self.value, 'to_dict'):
                result['data'] = self.value.to_dict()
            elif isinstance(self.value, dict):
                result['data'] = self.value
            elif isinstance(self.value, list):
                # Si c'est une liste, essayer de convertir chaque élément
                data_list = []
                for item in self.value:
                    if hasattr(item, 'to_dict'):
                        data_list.append(item.to_dict())
                    else:
                        data_list.append(item)
                result['data'] = data_list
            else:
                result['data'] = self.value
        
        if not self.success:
            result['error'] = self.error
            
        if self.details:
            result['details'] = self.details
            
        return result