# flask_app/models/ldap/users/user_utils.py
import unicodedata
import json
from ldap3 import SUBTREE
from ..base import LDAPBase


class LDAPUserUtils(LDAPBase):
    
    def generate_unique_cn(self, given_name, sn):
        original_sn = sn

        with open('flask_app/config/prefix.json', 'r') as f:
            prefix_list = json.load(f)
    
        # Sort prefixes by length in descending order (longest first)
        prefix_list.sort(key=lambda x: len(x.get('prefix', '')), reverse=True)
    
        for prefix_obj in prefix_list:
            prefix = prefix_obj.get('prefix', '')
            if prefix and sn.lower().startswith(prefix.lower()):
                sn = sn[len(prefix):].strip()
                break
    
        # If surname becomes empty after prefix removal (rare edge case)
        if not sn:
            sn = original_sn
    
        # Construct initial CN with first 3 chars of given_name and first 3 chars of sn (without prefix)
        # Handle short names gracefully
        first_part = given_name[:min(3, len(given_name))]
        second_part = sn[:min(3, len(sn))]
        cn_temp = f"{first_part}{second_part}"
    
        # Function to normalize and format in uppercase
        def normalize_cn(cn_string):
            normalized = unicodedata.normalize('NFD', cn_string)
            return ''.join(c for c in normalized if c.isalnum() and not unicodedata.combining(c)).upper()
    
        # Normalize the initial CN for the search
        cn = normalize_cn(cn_temp)
    
        # Check for uniqueness
        conn = self._get_connection()
        i = 2
    
        while True:
            # Check if CN already exists
            search_result = conn.search(
                search_base=self.all_users_dn,
                search_filter=f'(cn={cn})',
                search_scope=SUBTREE
            )
        
            # If CN doesn't exist, return it
            if not conn.entries:
                break
        
            # If we've exhausted all available characters in the surname
            i += 1
            if i >= len(original_sn):
                print("All surname characters have been tried. Creating a 5-character CN.")
                # Create a 5-char CN (3 from given name + 2 from surname)
                cn_temp = f"{given_name[:min(3, len(given_name))]}{sn[:min(2, len(sn))]}"
                cn = normalize_cn(cn_temp)
                break
        
            # Generate a new CN by replacing the 3rd character of the second part with the next character from surname
            if len(sn) > 2:  # Make sure surname has at least 3 chars
                new_sn = sn[:2] + original_sn[i]
            else:
                new_sn = sn + original_sn[i]
        
            cn_temp = f"{first_part}{new_sn}"
            cn = normalize_cn(cn_temp)
    
        conn.unbind()
        print(f"Final CN: {cn}")
        return cn
   
    def generate_password_from_cn(self, cn, short_name=False):
        if len(cn) < 5:
            # Handle case with very short CN
            return cn + 'x4$*987'  # Added extra complexity
        
        # Check if short_name flag is True
        if short_name:
            # Add extra complexity to avoid password containing the original short name
            first_part = cn[:3]
            if len(cn) == 5:
                second_part = cn[3:] + 'x3'  # Add extra characters
            else:
                second_part = cn[3:6] + 'x3'  # Add extra characters
                
            return (second_part + first_part[0:2]).lower() + '$*987'
        else:
            # Original logic for normal names
            if len(cn) == 5:
                # For 5-character CN, swap first 3 with last 2
                first_part = cn[:3]
                second_part = cn[3:]
                return (second_part + first_part).lower() + '*987'
            else:
                # For 6+ character CN, swap first 3 with next 3
                first_part = cn[:3]
                second_part = cn[3:6]
                return (second_part + first_part).lower() + '*987'
    
    def check_name_combination_exists(self, given_name, sn):
        try:
            conn = self._get_connection()
            
            # Create a search filter that combines both first name and last name
            search_filter = f'(&(givenName={given_name})(sn={sn}))'
            
            # Search in the users container
            search_base = self.all_users_dn
            
            conn.search(search_base=search_base,
                       search_filter=search_filter,
                       search_scope=SUBTREE,
                       attributes=['cn', 'givenName', 'sn', 'fullName'])
            
            if conn.entries:
                # User already exists, return the first matching user's DN
                user_dn = conn.entries[0].entry_dn
                conn.unbind()
                return True, user_dn
            
            conn.unbind()
            return False, ""
            
        except Exception as e:
            print(f"An error occurred while checking for name combination: {str(e)}")
            return False, ""
    
    def check_favvnatnr_exists(self, favvnatnr):
        try:
            conn = self._get_connection()
        
            # Normaliser le FavvNatNr (enlever espaces et tirets)
            normalized_favvnatnr = favvnatnr.replace(' ', '').replace('-', '')
        
            # Créer un filtre de recherche pour le FavvNatNr
            search_filter = f'(FavvNatNr={normalized_favvnatnr})'
        
            # Rechercher dans le conteneur d'utilisateurs
            search_base = self.all_users_dn
        
            conn.search(search_base=search_base,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=['cn', 'FavvNatNr', 'fullName'])
        
            if conn.entries:
                # L'utilisateur existe déjà, retourner le DN du premier utilisateur correspondant
                user_dn = conn.entries[0].entry_dn
                fullname = conn.entries[0].fullName.value if hasattr(conn.entries[0], 'fullName') else "Unknown"
                conn.unbind()
                return True, user_dn, fullname
        
            conn.unbind()
            return False, "", ""
        
        except Exception as e:
            print(f"Une erreur s'est produite lors de la vérification du FavvNatNr: {str(e)}")
            return False, "", ""