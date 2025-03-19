# flask_app/infrastructure/persistence/ldap/ldap_template_repo.py
from typing import List, Optional, Dict, Any
from flask_app.domain.repositories.template_repository import TemplateRepository
from flask_app.domain.models.template import Template
from flask_app.domain.models.result import Result
from flask_app.infrastructure.persistence.ldap.ldap_connection import LDAPConnection
from ldap3 import SUBTREE


class LDAPTemplateRepository(TemplateRepository):
    """
    Implémentation LDAP pour le repository de templates utilisateur.
    Cette classe implémente les méthodes définies dans l'interface TemplateRepository
    en utilisant le protocole LDAP pour interagir avec le serveur d'annuaire.
    """
    
    def __init__(self, connection_provider):
        """
        Initialise le repository avec un fournisseur de connexion LDAP.
        
        Args:
            connection_provider: Fournisseur de connexion LDAP qui gère le pool de connexions
        """
        self.connection_provider = connection_provider
        self.config = connection_provider.get_config()
    
    def get_template_details(self, template_cn: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un template spécifique.
        
        Args:
            template_cn: CN du template
            
        Returns:
            Détails du template ou None si non trouvé
        """
        conn = self.connection_provider.get_connection()
        try:
            search_base = self.config['template_dn']  # Base DN pour les templates
            
            # Échapper les caractères spéciaux pour LDAP
            search_term_escaped = self._escape_ldap_filter(template_cn)
            
            conn.search(
                search_base=search_base,
                search_filter=f'(cn={search_term_escaped})',
                search_scope=SUBTREE,
                attributes=['cn', 'description', 'title', 'objectClass', 'ou', 
                            'FavvExtDienstMgrDn', 'FavvEmployeeType', 'FavvEmployeeSubType',
                            'groupMembership']
            )
            
            if conn.entries:
                entry = conn.entries[0]
                template_data = {
                    'cn': entry.cn.value if hasattr(entry, 'cn') else None,
                    'dn': entry.entry_dn,
                    'description': entry.description.value if hasattr(entry, 'description') and entry.description else None,
                    'title': entry.title.value if hasattr(entry, 'title') and entry.title else None,
                    'objectClass': entry.objectClass.values if hasattr(entry, 'objectClass') and entry.objectClass else [],
                    'ou': entry.ou.value if hasattr(entry, 'ou') and entry.ou else None,
                    'FavvExtDienstMgrDn': entry.FavvExtDienstMgrDn.value if hasattr(entry, 'FavvExtDienstMgrDn') and entry.FavvExtDienstMgrDn else None,
                    'FavvEmployeeType': entry.FavvEmployeeType.value if hasattr(entry, 'FavvEmployeeType') and entry.FavvEmployeeType else None,
                    'FavvEmployeeSubType': entry.FavvEmployeeSubType.value if hasattr(entry, 'FavvEmployeeSubType') and entry.FavvEmployeeSubType else None,
                    'groupMembership': []
                }
                
                # Récupérer les groupes associés au template
                if hasattr(entry, 'groupMembership') and entry.groupMembership:
                    group_dns = entry.groupMembership.values
                    
                    # Pour chaque DN de groupe, récupérer le CN
                    for group_dn in group_dns:
                        try:
                            conn.search(
                                search_base=group_dn,
                                search_filter='(objectClass=*)',
                                search_scope='BASE',
                                attributes=['cn']
                            )
                            
                            if conn.entries:
                                group_cn = conn.entries[0].cn.value
                                template_data['groupMembership'].append({
                                    'dn': group_dn,
                                    'cn': group_cn
                                })
                            else:
                                # Si le groupe n'est pas trouvé, ajouter uniquement le DN
                                template_data['groupMembership'].append({
                                    'dn': group_dn,
                                    'cn': group_dn.split(',')[0].split('=')[1] if '=' in group_dn else 'Unknown'
                                })
                        except Exception as e:
                            print(f"Erreur lors de la récupération des détails du groupe {group_dn}: {str(e)}")
                
                # Si le template a un manager, récupérer son nom
                if template_data['FavvExtDienstMgrDn']:
                    try:
                        conn.search(
                            search_base=template_data['FavvExtDienstMgrDn'],
                            search_filter='(objectClass=*)',
                            search_scope='BASE',
                            attributes=['fullName']
                        )
                        
                        if conn.entries and hasattr(conn.entries[0], 'fullName'):
                            template_data['ServiceManagerName'] = conn.entries[0].fullName.value
                        else:
                            template_data['ServiceManagerName'] = "Nom non trouvé"
                    except Exception as e:
                        print(f"Erreur lors de la récupération du nom du manager: {str(e)}")
                        template_data['ServiceManagerName'] = "Erreur de recherche"
                
                return template_data
            
            return None
            
        except Exception as e:
            print(f"Erreur lors de la récupération des détails du template: {str(e)}")
            return None
        finally:
            self.connection_provider.release_connection(conn)
    
    def get_user_types(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les types d'utilisateur disponibles.
        
        Returns:
            Liste des types d'utilisateur avec leurs descriptions
        """
        conn = self.connection_provider.get_connection()
        try:
            search_base = self.config['template_dn']
            attributes = ['cn', 'description', 'title']
            
            conn.search(
                search_base=search_base,
                search_filter='(objectClass=template)',
                search_scope=SUBTREE,
                attributes=attributes
            )
            
            # Utiliser un dictionnaire pour assurer l'unicité par cn
            unique_types = {}
            for entry in conn.entries:
                if hasattr(entry, 'description') and entry.description:
                    title_value = entry.title.value if hasattr(entry, 'title') and entry.title else None
                    unique_types[entry.cn.value] = {
                        'description': entry.description.value,
                        'title': title_value
                    }
            
            # Convertir en liste de dictionnaires pour le format attendu
            user_types = [
                {
                    'value': cn, 
                    'label': data['description'], 
                    'title': data['title']
                } 
                for cn, data in unique_types.items()
            ]
            
            return user_types
            
        except Exception as e:
            print(f"Erreur lors de la récupération des types d'utilisateur: {str(e)}")
            return []
        finally:
            self.connection_provider.release_connection(conn)
    
    def _escape_ldap_filter(self, input_string: str) -> str:
        """
        Échappe les caractères spéciaux dans un filtre LDAP.
        
        Args:
            input_string: Chaîne d'entrée à échapper
            
        Returns:
            Chaîne échappée pour filtre LDAP
        """
        if not input_string:
            return ""
        
        # Échapper les caractères spéciaux selon la RFC 2254
        special_chars = {
            '\\': r'\5c',
            '*': r'\2a',
            '(': r'\28',
            ')': r'\29',
            '\0': r'\00'
        }
        
        result = input_string
        for char, replacement in special_chars.items():
            result = result.replace(char, replacement)
        
        return result