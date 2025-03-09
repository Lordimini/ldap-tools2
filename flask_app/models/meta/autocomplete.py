# flask_app/models/ldap/autocomplete.py
from .base import METABase
from ldap3 import Connection

class METAAutocompleteMixin(METABase):
    def autocomplete(self, search_type, search_term):
        """
        Fonction d'autocomplete unifiée supportant différents types de recherche.
        
        Parameters:
        -----------
        search_type : str
            Type de recherche à effectuer ('group', 'fullName', 'role', 'services', 'managers')
        search_term : str
            Terme de recherche à utiliser pour l'autocomplete
                
        Returns:
        --------
        list
            Liste de dictionnaires contenant les résultats d'autocomplete avec 'label' et 'value'
        """
        # Validation initiale
        if not search_term or not search_type:
            return []
                
        # Ne pas effectuer de recherche si le terme est trop court (uniquement pour fullName)
        if search_type == 'fullName' and len(search_term) < 3:
            return []
        
        # Utiliser les fonctions dédiées pour les cas spéciaux
        if search_type == 'roles' or search_type == 'role':
            return self.autocomplete_role(search_term)
        elif search_type == 'services':
            return self.autocomplete_services(search_term)
        
        # Échapper les caractères spéciaux pour LDAP si nécessaire
        search_term_escaped = self._escape_ldap_filter(search_term) if hasattr(self, '_escape_ldap_filter') else search_term
        
        try:
            # Obtenir une connexion LDAP
            if hasattr(self, '_get_connection'):
                conn = self._get_connection()
            else:
                conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            results = []
            
            # Configuration spécifique selon le type de recherche
            if search_type == 'group':
                for base_dn in [self.base_dn, self.app_base_dn]:
                    conn.search(base_dn, f'(cn=*{search_term_escaped}*)', 
                            search_scope='SUBTREE', attributes=['cn'])
                    
                    for entry in conn.entries:
                        if ('cn=UserApplication,cn=DS4,ou=SYSTEM,o=COPY' not in entry.entry_dn):
                            results.append({
                                'label': f"{entry.cn.value} ({entry.entry_dn})",
                                'value': entry.cn.value
                            })
                            
            elif search_type == 'fullName':
                ldap_filter = f'(&(objectClass=Person)(fullName=*{search_term_escaped}*))'
                attributes = ['cn', 'fullName']
                
                conn.search(
                    search_base=self.all_users_dn,
                    search_filter=ldap_filter,
                    search_scope='SUBTREE',
                    attributes=attributes,
                    size_limit=20,
                    time_limit=5
                )
                
                for entry in conn.entries:
                    if hasattr(entry, 'fullName') and entry.fullName.value:
                        results.append({
                            'label': entry.fullName.value,
                            'value': entry.fullName.value
                        })
                
                # Limiter à 20 résultats
                results = results[:20]
                    
            elif search_type == 'managers':
                search_base = self.actif_users_dn
                search_filter = f'(&(FavvDienstHoofd=YES)(fullName=*{search_term_escaped}*))'
                
                conn.search(
                    search_base=search_base,
                    search_filter=search_filter,
                    search_scope='SUBTREE',
                    attributes=['cn', 'fullName', 'title', 'mail']
                )
                
                for entry in conn.entries:
                    results.append({
                        'label': f"{entry.fullName.value} - {entry.mail.value if hasattr(entry, 'mail') and entry.mail else 'No email'} - {entry.title.value if hasattr(entry, 'title') and entry.title else 'No title'}",
                        'value': entry.fullName.value
                    })
            
            else:
                # Type de recherche non reconnu
                return []
                    
            # Fermer la connexion
            conn.unbind()
            return results
                
        except Exception as e:
            print(f"Erreur lors de l'autocomplétion ({search_type}): {str(e)}")
            return []
            
    def autocomplete_role(self, search_term):
        """
        Fonction d'autocomplétion spécifique pour les rôles, avec validation des DNs.
        """
        try:
            conn = Connection(self.meta_server, user=self.bind_dn, 
                            password=self.password, auto_bind=True)
            
            roles = []
            
            # Vérifier que role_base_dn est bien une liste
            base_dns = self.role_base_dn if isinstance(self.role_base_dn, list) else [self.role_base_dn]
            
            # Exécuter la recherche pour chaque base_dn valide
            for base_dn in base_dns:
                # Vérifier que le base_dn est valide
                if not base_dn or not isinstance(base_dn, str) or '=' not in base_dn:
                    print(f"Base DN invalide ignoré: {base_dn}")
                    continue
                    
                try:
                    print(f"Recherche de rôles dans {base_dn} avec filtre: (cn=*{search_term}*)")
                    conn.search(base_dn, f'(cn=*{search_term}*)', 
                            search_scope='SUBTREE', 
                            attributes=['cn'])
                    
                    # Traiter les entrées trouvées dans ce base_dn
                    for entry in conn.entries:
                        if hasattr(entry, 'cn') and entry.cn:
                            label = f"{entry.cn.value}" if hasattr(entry.cn, 'value') else "Unknown"
                            if hasattr(entry, 'entry_dn'):
                                label += f" ({entry.entry_dn})"
                            
                            roles.append({
                                'label': label,
                                'value': entry.cn.value if hasattr(entry.cn, 'value') else entry.entry_dn
                            })
                except Exception as e:
                    print(f"Erreur lors de la recherche dans {base_dn}: {str(e)}")
                    # Continuer avec le prochain base_dn en cas d'erreur
                    continue
            
            print(f"Nombre total de rôles trouvés: {len(roles)}")
            
            conn.unbind()
            return roles
            
        except Exception as e:
            import traceback
            print(f"Erreur lors de l'autocomplétion des rôles: {str(e)}")
            print(traceback.format_exc())
            return []
        
    def autocomplete_services(self, search_term):
        """
        Fournit une fonctionnalité d'autocomplétion pour les services (OU),
        avec élimination des doublons et validation des DNs.
        
        Args:
            search_term (str): Terme de recherche pour filtrer les services
            
        Returns:
            list: Liste des services correspondant au terme de recherche
        """
        try:
            conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Échapper le terme de recherche
            search_term_escaped = self._escape_ldap_filter(search_term) if hasattr(self, '_escape_ldap_filter') else search_term
            
            # Dictionnaire pour éliminer les doublons (clé = valeur du service en minuscules)
            unique_services = {}
            
            # Bases DN à rechercher
            base_dns = [self.app_base_dn, self.base_dn]
            
            # Parcourir toutes les bases DN
            for base_dn in base_dns:
                # Vérifier que le base_dn est valide
                if not base_dn or not isinstance(base_dn, str) or '=' not in base_dn:
                    print(f"Base DN invalide ignoré dans autocomplete_services: {base_dn}")
                    continue
                    
                try:
                    # Limiter la recherche pour de meilleures performances
                    conn.search(
                        base_dn, 
                        f'(ou=*{search_term_escaped}*)', 
                        search_scope='SUBTREE', 
                        attributes=['ou'],
                        size_limit=50,  # Limiter le nombre de résultats
                        time_limit=5     # Limiter le temps de recherche en secondes
                    )
                    
                    # Ajouter chaque service unique au dictionnaire
                    for entry in conn.entries:
                        if hasattr(entry, 'ou') and entry.ou and entry.ou.value:
                            # Utiliser la valeur en minuscules comme clé pour éviter les doublons
                            service_value = entry.ou.value
                            service_key = service_value.lower()
                            
                            # Ajouter seulement si ce service n'existe pas déjà
                            if service_key not in unique_services:
                                unique_services[service_key] = {
                                    'label': service_value,
                                    'value': service_value
                                }
                except Exception as e:
                    print(f"Erreur lors de la recherche dans {base_dn}: {str(e)}")
                    # Continuer avec le prochain base_dn en cas d'erreur
                    continue
            
            # Convertir le dictionnaire en liste pour le retour
            services = list(unique_services.values())
            
            # Trier les services par ordre alphabétique
            services.sort(key=lambda x: x['label'])
            
            # Limiter le nombre de résultats retournés
            services = services[:20]
            
            # Fermer la connexion
            conn.unbind()
            return services
                
        except Exception as e:
            import traceback
            print(f"Erreur lors de l'autocomplétion des services: {str(e)}")
            print(traceback.format_exc())
            if 'conn' in locals() and conn:
                conn.unbind()
            return []