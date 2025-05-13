# flask_app/models/ldap/services.py
from .base import METABase
from ldap3 import Connection, SUBTREE

class METAServiceMixin(METABase):
    def get_service_users(self, service_name):
        """
        Récupère les utilisateurs d'un service donné, avec validation des DNs.
        
        Args:
            service_name (str): Nom du service (ou) à rechercher
            
        Returns:
            dict: Dictionnaire contenant le nom du service et la liste des utilisateurs
        """
        try:
            users = []
            conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # S'assurer que actif_users_dn est une liste
            base_dns = self.actif_users_dn if isinstance(self.actif_users_dn, list) else [self.actif_users_dn]
            
            # Échapper le service_name pour éviter les injections LDAP
            service_name_escaped = self._escape_ldap_filter(service_name) if hasattr(self, '_escape_ldap_filter') else service_name
            
            # Parcourir tous les base_dn valides
            for base_dn in base_dns:
                # Vérifier que le base_dn est valide
                if not base_dn or not isinstance(base_dn, str) or '=' not in base_dn:
                    print(f"Base DN invalide ignoré dans get_service_users: {base_dn}")
                    continue
                    
                try:
                    print(f"Recherche des utilisateurs du service '{service_name}' dans {base_dn}")
                    conn.search(base_dn, 
                            f'(ou={service_name_escaped})', 
                            search_scope='SUBTREE',
                            attributes=['cn', 'fullName', 'title', 'mail'])
                    
                    # Traiter les résultats
                    for entry in conn.entries:
                        users.append({
                            'CN': entry.cn.value if hasattr(entry, 'cn') and entry.cn else 'Unknown',
                            'fullName': entry.fullName.value if hasattr(entry, 'fullName') and entry.fullName else 'Unknown',
                            'title': entry.title.value if hasattr(entry, 'title') and entry.title else 'N/A',
                            'mail': entry.mail.value if hasattr(entry, 'mail') and entry.mail else 'N/A'
                        })
                except Exception as e:
                    print(f"Erreur lors de la recherche dans {base_dn}: {str(e)}")
                    # Continuer avec le prochain base_dn en cas d'erreur
                    continue

            if users:
                result = {
                    'service_name': service_name,
                    'users': users
                }
            else:
                result = None
                print(f"Aucun utilisateur trouvé pour le service: {service_name}")

            # Fermer la connexion
            conn.unbind()
            return result
                
        except Exception as e:
            import traceback
            print(f"Erreur dans get_service_users: {str(e)}")
            print(traceback.format_exc())
            if 'conn' in locals() and conn:
                conn.unbind()
            return None
        
    def get_managers(self):
        """
        Récupère la liste des utilisateurs ayant FavvDienstHoofd=YES
    
        Returns:
        list: Liste des utilisateurs chefs hiérarchiques avec leur fullName et DN
        """
        try:
            conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True)
        
            # Rechercher les utilisateurs avec FavvDienstHoofd=YES
            search_base = self.actif_users_dn
            search_filter = '(FavvDienstHoofd=YES)'
        
            conn.search(search_base=search_base,
                        search_filter=search_filter,
                        search_scope=SUBTREE,
                        attributes=['cn', 'fullName', 'title', 'mail'])
        
            managers = []
            for entry in conn.entries:
                managers.append({
                    'dn': entry.entry_dn,
                    'fullName': entry.fullName.value if entry.fullName else '',
                    'title': entry.title.value if entry.title else '',
                    'mail': entry.mail.value if entry.mail else ''
                })
        
            conn.unbind()
            return managers
        
        except Exception as e:
            print(f"Erreur lors de la récupération des chefs hiérarchiques: {str(e)}")
            return []
    
    # ... autres méthodes liées aux services