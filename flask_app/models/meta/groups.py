# flask_app/models/ldap/groups.py
from .base import METABase
from ldap3 import Connection

class METAGroupMixin(METABase):
    
    def get_group_users(self, group_name):
        conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True) 
        group_dn = None
        for base_dn in ['ou=Groups,ou=IAM-Security,o=COPY', self.app_base_dn, 'ou=GROUPS,ou=SYNC,o=COPY']:
            conn.search(base_dn, f'(cn={group_name})', search_scope='SUBTREE', attributes=['cn'])
            if conn.entries:
                group_dn = conn.entries[0].entry_dn
                break

        if group_dn:
            # Fetch the group's members
            conn.search(group_dn, '(objectClass=*)', attributes=['member'])
            if conn.entries and conn.entries[0].member:
                members = conn.entries[0].member.values
                users = []
                # Fetch details for each member
                for member_dn in members:
                    conn.search(member_dn, '(objectClass=*)', attributes=['cn', 'fullName', 'title', 'ou'])
                    if conn.entries:
                        user = conn.entries[0]
                        users.append({
                            'CN': user.cn.value,
                            'fullName': user.fullName.value,
                            'title': user.title.value if user.title else 'N/A',
                            'service': user.ou.value if user.ou else 'N/A'
                        })
                    else:
                        print(f"User not found for DN: {member_dn}")
                result = {
                    'group_name': group_name,
                    'group_dn': group_dn,
                    'users': users
                }
            else:
                result = {
                    'group_name': group_name,
                    'group_dn': group_dn,
                    'users': []
                }
                flash('Group has no members.', 'info')
        else:
            result = None
            flash('Group not found.', 'danger')

        # Unbind the connection
        conn.unbind()
        return result
        
    def get_group_users_by_dn(self, group_dn, group_name=None):
        """
        Récupère les utilisateurs d'un groupe en utilisant son DN complet.
        
        Args:
            group_dn (str): DN complet du groupe
            group_name (str, optional): Nom du groupe (pour l'affichage)
            
        Returns:
            dict: Informations sur le groupe et ses utilisateurs
        """
        try:
            conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # Vérifier si le groupe existe
            conn.search(group_dn, '(objectClass=*)', search_scope='BASE', attributes=['cn'])
            
            if not conn.entries:
                print(f"Group with DN '{group_dn}' not found")
                return None
                
            # Utiliser le CN du groupe si group_name n'est pas fourni
            if not group_name and conn.entries:
                group_name = conn.entries[0].cn.value
            
            # Récupérer les membres du groupe
            conn.search(group_dn, '(objectClass=*)', attributes=['member'])
            
            users = []
            if conn.entries and hasattr(conn.entries[0], 'member') and conn.entries[0].member:
                members = conn.entries[0].member.values
                
                # Récupérer les détails de chaque membre
                for member_dn in members:
                    try:
                        conn.search(member_dn, '(objectClass=*)', attributes=['cn', 'fullName', 'title', 'ou'])
                        if conn.entries:
                            user = conn.entries[0]
                            users.append({
                                'CN': user.cn.value if hasattr(user, 'cn') else 'Unknown',
                                'fullName': user.fullName.value if hasattr(user, 'fullName') else 'Unknown',
                                'title': user.title.value if hasattr(user, 'title') else 'N/A',
                                'service': user.ou.value if hasattr(user, 'ou') else 'N/A'
                            })
                    except Exception as e:
                        print(f"Error fetching user details for {member_dn}: {str(e)}")
            
            # Créer le résultat
            result = {
                'group_name': group_name,
                'group_dn': group_dn,
                'users': users
            }
            
            conn.unbind()
            return result
            
        except Exception as e:
            import traceback
            print(f"Error in get_group_users_by_dn: {str(e)}")
            print(traceback.format_exc())
            if 'conn' in locals() and conn:
                conn.unbind()
            return None
        
    def add_user_to_group(self, user_dn, group_dn):
        """
        Ajoute un utilisateur à un groupe et met à jour les attributs correspondants
        
        Parameters:
        user_dn (str): DN de l'utilisateur à ajouter
        group_dn (str): DN du groupe auquel ajouter l'utilisateur
        
        Returns:
        bool: True si l'opération a réussi, False sinon
        """
        try:
            # Établir une connexion au serveur LDAP
            conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # 1. Ajouter le DN du groupe à l'attribut groupMembership de l'utilisateur
            user_modify = conn.modify(
                user_dn, 
                {'groupMembership': [(MODIFY_ADD, [group_dn])]}
            )
            
            # 2. Ajouter le DN de l'utilisateur à l'attribut member du groupe
            group_modify = conn.modify(
                group_dn, 
                {'member': [(MODIFY_ADD, [user_dn])]}
            )
            
            # 3. Ajouter le DN de l'utilisateur à l'attribut equivalentToMe du groupe (si c'est un groupe de type rôle)
            # Vérifions d'abord si c'est un groupe de type rôle
            conn.search(group_dn, '(objectClass=nrfRole)', search_scope='BASE')
            if conn.entries:
                # C'est un groupe de type rôle, mettons à jour equivalentToMe
                equiv_modify = conn.modify(
                    group_dn, 
                    {'equivalentToMe': [(MODIFY_ADD, [user_dn])]}
                )
            else:
                # Pas un groupe de type rôle, pas besoin de mettre à jour equivalentToMe
                equiv_modify = True
            
            # Vérifier si toutes les opérations ont réussi
            success = user_modify and group_modify and equiv_modify
            
            # Fermer la connexion
            conn.unbind()
            
            return success
        
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'utilisateur au groupe: {str(e)}")
            return False
    
    def remove_user_from_group(self, user_dn, group_dn):
        """
        Supprime un utilisateur d'un groupe.
        
        Args:
            user_dn (str): DN de l'utilisateur à supprimer
            group_dn (str): DN du groupe duquel supprimer l'utilisateur
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Établir une connexion au serveur LDAP
            conn = Connection(self.meta_server, user=self.bind_dn, password=self.password, auto_bind=True)
            
            # 1. Supprimer le DN du groupe de l'attribut groupMembership de l'utilisateur
            conn.modify(
                user_dn, 
                {'groupMembership': [(MODIFY_DELETE, [group_dn])]}
            )
            
            # 2. Supprimer le DN de l'utilisateur de l'attribut member du groupe
            conn.modify(
                group_dn, 
                {'member': [(MODIFY_DELETE, [user_dn])]}
            )
            
            # 3. Supprimer le DN de l'utilisateur de l'attribut equivalentToMe du groupe (si c'est un groupe de type rôle)
            conn.search(group_dn, '(objectClass=nrfRole)', search_scope='BASE')
            if conn.entries:
                conn.modify(
                    group_dn, 
                    {'equivalentToMe': [(MODIFY_DELETE, [user_dn])]}
                )
            
            # Fermer la connexion
            conn.unbind()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la suppression de l'utilisateur du groupe: {str(e)}")
            return False
    
    # ... autres méthodes liées aux groupes