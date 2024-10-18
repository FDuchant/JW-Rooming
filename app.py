import config
from datetime import datetime, timedelta
import json
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
from pathlib import Path
import pytz
import requests
from   requests.auth import HTTPBasicAuth
import ssl
import streamlit as st


#################################################################
### AFD Comment - START - Set of Functions to load JSON files ###
#################################################################
def load_data(file_name):
    try:
        with open(file_name, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"AFD - ERROR : Issue in 'load_config' function. File path concerned : {file_name}")
        return False
###############################################################
### AFD Comment - END - Set of Functions to load JSON files ###
###############################################################



#################################################################
### AFD Comment - START - Set of Functions to print JSON data ###
#################################################################
def print_pretty_json_from_memory(json_data):
    try:
        pretty_json = json.dumps(json_data, indent=4, ensure_ascii=False)
        print(pretty_json)
    except:
        print(f"AFD - ERROR : in function print_pretty_json_from_memory")
#################################################################
### AFD Comment - END - Set of Functions to print JSON data ###
#################################################################



####################################################################
### AFD Comment - START - Set of Functions to handle JSON MATRIX ###
####################################################################
def get_value_from_matrix_by_tag(json_matrix, ref_tag, ref_value, searched_tag):
    try:
        for user in json_matrix:
            if user.get(ref_tag) == ref_value:
                return user.get(searched_tag)
        return None
    except Exception as e:
        logging.error(f"ERROR : in function get_value_from_matrix_by_tag: {e}")
        return None
##################################################################
### AFD Comment - END - Set of Functions to handle JSON MATRIX ###
##################################################################



####################################################################
### AFD Comment - START - Set of Functions to handle DATE FORMAT ###
####################################################################
def format_date_add_delay(date_ori, delay):
    try:
        date_str = date_ori
        date_obj = datetime.strptime(date_str, "%Y-%m-%d") # Conversion de la chaîne de caractères en objet datetime
        date_obj += timedelta(days=delay) # Ajout de journées
        timezone = pytz.timezone('Europe/Paris') # Définition du fuseau horaire (+02:00)
        localized_date = timezone.localize(date_obj) # Localisation de l'objet datetime avec le fuseau horaire
        formatted_date = localized_date.isoformat() # Affichage de la date avec le format souhaité
        return formatted_date
    except Exception as e:
        logging.error(f"ERROR : in function format_date_add_delay: {e}")
        logging.error(f"ERROR : during data format (+)")
        return False


def format_date_delete_delay(date_ori, delay):
    try:
        date_str = date_ori
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        date_obj -= timedelta(days=delay)
        timezone = pytz.timezone('Europe/Paris')
        localized_date = timezone.localize(date_obj)
        formatted_date = localized_date.isoformat()
        return formatted_date
    except Exception as e:
        logging.error(f"ERROR : in function format_date_delete_delay: {e}")
        logging.error(f"ERROR : during data format (-)")
        return False
####################################################################
### AFD Comment - START - Set of Functions to handle DATE FORMAT ###
####################################################################




##########################################################################
### AFD Comment - START - Set of Functions to add ROOM BLOCK in JW Hub ###
##########################################################################
def add_room_block(base_url, JWToken, JWCookie, json_content):
    try:
        api_url = base_url + 'rooming/api/roomblocks' #post Users request
        header = {'X-XSRF-TOKEN': JWToken, 'accept': 'application/json', 'Content-Type': 'application/json', 'cookie': JWCookie}
        response = requests.post(url=api_url, json=json_content, headers=header)

        if response.status_code == 200: ### USER SUCCESSFULLY CREATED ###
            response_data = response.json()
            blockID = response_data.get("roomBlockGuid")
            print(f"INFO : Roomblock correctement créé - NEW BLOCK ID : {blockID}")
            st.success(f"SUCCES : Roomblock correctement créé - NEW BLOCK ID : {blockID}")
        else:
            print(f"ERROR : ROOMBLOCK NON CREE")
            response_data = response.json()
            print_pretty_json_from_memory(response.json())
            ErrorTitle = response_data.get("title")
            st.info(f"ERREUR : l'un des blocs n'a pas été créé - vérifiez qu'il n'y a pas déjà des blocs existants pour cet assembléee dans cet hotel")
            st.info(f"ERREUR : l'un des blocs n'a pas été créé - rappellez vous qu'il n'est pas possible d'avoir une valeur nulle (0) lors de la création du lot")
            st.info(f"ERREUR : l'un des blocs n'a pas été créé - assurez vous que le nombre de chambre pour une journée ne dépasse pas la taille maximum défini au contrat")
            st.error(f"ERROR : creation d'un des blocs de chambre IMPOSSIBLE - Vérifiez sur JW Hub les blocs créés pour cet hotel - Description de l'Erreur : {ErrorTitle}")
    except requests.exceptions.RequestException as e:
        print(f"AFD - ERROR : in function add_room_block : {e}")
        print_pretty_json_from_memory(response.json())


def create_json_rooming_block_sizes(room_reservation_data, event_start_date): 
    try:
        json_rooming_block_sizes = []
        rooming_thurday_date = format_date_delete_delay(event_start_date, 1)
        rooming_friday_date = format_date_add_delay(event_start_date, 0)
        rooming_saturday_date = format_date_add_delay(event_start_date, 1)
        rooming_sunday_date = format_date_add_delay(event_start_date, 2)

        thursday_room_type_block_size = 0
        friday_room_type_block_size = 0
        saturday_room_type_block_size = 0
        sunday_room_type_block_size = 0

        room_type_list = list(room_reservation_data.keys())
        for index in range(0, len(room_reservation_data)):
            room_type_name = room_type_list[index]
            room_type_id = get_value_from_matrix_by_tag(ROOMTYPE_MATRIX, 'description', room_type_name, 'eventRoomTypeGuid')
            thursday_room_type_block_size = room_reservation_data[room_type_name].get('Thursday')
            friday_room_type_block_size = room_reservation_data[room_type_name].get('Friday')
            saturday_room_type_block_size = room_reservation_data[room_type_name].get('Saturday')
            sunday_room_type_block_size = room_reservation_data[room_type_name].get('Sunday')

            json_blocksize = {
                "eventRoomTypeGuid":room_type_id,
                "blockSizesByDate":[
                                {"date": rooming_thurday_date,"size":thursday_room_type_block_size},
                                {"date": rooming_friday_date,"size":friday_room_type_block_size},
                                {"date": rooming_saturday_date,"size":saturday_room_type_block_size},
                                {"date": rooming_sunday_date,"size":sunday_room_type_block_size}]
            }
            json_rooming_block_sizes.append(json_blocksize)
        return json_rooming_block_sizes
    except Exception as e:
        print(f"AFD - ERROR : in function create_json_rooming_block_sizes - Error: {e}")


def create_json_rooming_assignments(own_assignment_data, event_start_date):
    try:
        json_own_assignment_sizes = []
        rooming_thurday_date = format_date_delete_delay(event_start_date, 1)
        rooming_friday_date = format_date_add_delay(event_start_date, 0)
        rooming_saturday_date = format_date_add_delay(event_start_date, 1)
        rooming_sunday_date = format_date_add_delay(event_start_date, 2)

        thursday_room_type_block_size = own_assignment_data.get("Thursday")
        friday_room_type_block_size = own_assignment_data.get("Friday")
        saturday_room_type_block_size = own_assignment_data.get("Saturday")
        sunday_room_type_block_size = own_assignment_data.get("Sunday")
    
        json_own_assignment_sizes = [
            {"date": rooming_thurday_date,"size":thursday_room_type_block_size},
            {"date": rooming_friday_date,"size":friday_room_type_block_size},
            {"date": rooming_saturday_date,"size":saturday_room_type_block_size},
            {"date": rooming_sunday_date,"size":sunday_room_type_block_size}
        ]
        return json_own_assignment_sizes
    except Exception as e:
        print(f"AFD - ERROR : in function create_json_rooming_assignments - Error: {e}")


def create_json_rooming_block(HotelID, ContractID, EventID, EventStartDate, blocsize_organization, organizator_assignment, block_activation_status):
    try:
        thursday_event_date = format_date_delete_delay(EventStartDate, 1)
        sunday_event_date = format_date_add_delay(EventStartDate, 2)
        cutoff_event_date = format_date_delete_delay(EventStartDate, 30)
        block_content = create_json_rooming_block_sizes(blocsize_organization, EventStartDate)
        organization_assignment = create_json_rooming_assignments(organizator_assignment, EventStartDate)
        json_rooming_block = {
                "eventGuid": EventID,
                "hotelGuid": HotelID,
                "audienceType": "localAttendees",
                "guestBranchGuids": [],
                "startDate": thursday_event_date,
                "endDate": sunday_event_date,
                "cutoffDate": cutoff_event_date,
                "contractGuid": ContractID,
                "blockSizes": block_content,
                "roomsOrganizationCanAssign": organization_assignment,
                "isOnRLL": block_activation_status
        }
        return json_rooming_block
    except Exception as e:
        print(f"AFD - ERROR : in function create_json_rooming_block - Error: {e}") 


def update_room_block():
    try:
        pass
        # request to get roomblock id list for one contract for all events
        #https://hub.jw.org/rooming/api/events/642dc84f-97d1-46f9-8497-fa4ec865bfa3/contracts/0175e9c5-ccf9-4e5a-bc16-7649dc1a9a69/roomBlocks
        # request to make roomblock update
        #https://hub.jw.org/rooming/api/roomblocks/e66df043-e4aa-416f-b207-73fdb95d5ea5/updateblocksizes
    except Exception as e:
        print(f"AFD - ERROR : in function update_room_block - Error: {e}")
########################################################################
### AFD Comment - END - Set of Functions to add ROOM BLOCK in JW Hub ###
########################################################################




############################################################################
### AFD Comment - START - Set of Functions to read some data from JW Hub ###
############################################################################
### Function to get events (convention) data from JW Hub ###
def get_all_events_data(base_url, JWToken, JWCookie): 
    try:
        api_url = base_url + 'event-management/api/types/events?includePast=false&eventTypeGroup=regional-conventions' #post Users request
        #api_url = 'https://hub.jw.org/event-management/api/types/events?includePast=false&eventTypeGroup=regional-conventions&languageGuid=c6d09e3c-9644-4f06-ac58-8c146429474e'
        header = {
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate, br, zstd',
                    'Accept-Language': 'fr',
                    'Connection': 'keep-alive',
                    'Cookie': JWCookie,
                    'Host': 'hub.jw.org',
                    'Referer': 'https://hub.jw.org/event-management/fr/types/regional-conventions',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                    'X-Client-Version': '2.37.0',
                    'X-Requested-With': 'cdh-application',
                    'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"macOS"'
                }
        response = requests.get(url=api_url, headers=header)
        if response.status_code == 200:
            response_data = response.json()
            #with open('reponse_api_AllEvent.json', 'w', encoding='utf-8') as file:
            #    json.dump(response_data, file, ensure_ascii=False, indent=4)  # 'indent=4' to help in reading
            simplified_event_list = []
            for event in response_data['events']:
                event_id = event.get('eventGuid', '')
                event_name = event.get('name', '')
                event_start_date = event.get('startDate', '')
                event_end_date = event.get('endDate', '')
                simplified_event = {
                    'eventGuid': event_id,
                    'name': event_name,
                    'startDate': event_start_date,
                    'endDate': event_end_date
                }
                simplified_event_list.append(simplified_event)
            return simplified_event_list
    except requests.exceptions.RequestException as e:
        print(f"AFD - ERROR : API status code : {response.status_code}")
        print(f"AFD - ERROR : in function get_all_events_data : {e}")
        #print_pretty_json_from_memory(response_data)


### Function to get hotels and contracts data from first event on JW Hub ###
def get_all_hotels_data(base_url, JWToken, JWCookie, EventID): # GET LIST OF HOTELS (FROM FIRST EVENT)
    try:
        api_url = base_url + 'rooming/api/events/' + EventID + '/hotels/byevent'
        #api_url = 'https://hub.jw.org/rooming/api/events/642dc84f-97d1-46f9-8497-fa4ec865bfa3/hotels/byevent?languageGuid=c6d09e3c-9644-4f06-ac58-8c146429474e'
        header = {
                    'Accept': 'application/json', 
                    'Accept-Encoding': 'gzip, deflate, br, zstd', 
                    'Accept-language': 'fr',
                    'Connection': 'keep-alive',
                    'Cookie': JWCookie,
                    'Host': 'hub.jw.org', 
                    'Refer': 'https://hub.jw.org/rooming/events/' + EventID + '/overview', 
                    'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"macOS"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                    'X-client-version': '3.44.1',
                    'X-requested-with': 'cdh-application',
                  }

        response = requests.get(url=api_url, headers=header)
        if response.status_code == 200:
            simplified_hotel_list = []
            contracted_hotel_list = []
            response_data = response.json()
            #with open('reponse_api_AllHotel.json', 'w', encoding='utf-8') as file:
            #    json.dump(response_data, file, ensure_ascii=False, indent=4)  # 'indent=4' pour une bonne lisibilité

            for hotel in response_data['hotels']:
                hotel_id = hotel.get('hotelGuid', '')
                hotel_name = hotel.get('hotelName', '')
                simplified_hotel = {
                    'hotelGuid' : hotel_id,
                    'hotelName' : hotel_name
                }
                simplified_hotel_list.append(simplified_hotel)

            for contract in response_data['contracts']:
                hotel_id = contract.get('hotelGuid', '')
                hotel_name = get_value_from_matrix_by_tag(simplified_hotel_list, 'hotelGuid', hotel_id, 'hotelName')
                hotel_room_types = contract.get('roomTypes', '')
                hotel_contract_id = contract.get('contractGuid', '')
                contracted_hotel = {
                    'hotelGuid' : hotel_id,
                    'hotelName' : hotel_name,
                    'contractGuid' : hotel_contract_id,
                    'roomTypes' : hotel_room_types
                }
                contracted_hotel_list.append(contracted_hotel)
        return contracted_hotel_list
    except requests.exceptions.RequestException as e:
        print(f"AFD - ERROR : in function get_all_hotels_data : {e}")
        #print_pretty_json_from_memory(response_data)


### Function to get roomtype data from JW Hub ###
def get_roomtype_matrix(base_url, JWCookie, EventID):
    try:
        if JWCookie and EventID:
            #https://hub.jw.org/rooming/api/roomtypes?languageGuid=c6d09e3c-9644-4f06-ac58-8c146429474e
            api_url = base_url + 'rooming/api/roomtypes?languageGuid=c6d09e3c-9644-4f06-ac58-8c146429474e'
            header = {
                    'Accept': 'application/json', 
                    'Accept-Encoding': 'gzip, deflate, br, zstd', 
                    'Accept-language': 'fr',
                    'Connection': 'keep-alive',
                    'Cookie': JWCookie,
                    'Host': 'hub.jw.org', 
                    'Refer': 'https://hub.jw.org/rooming/events/' + EventID + '/hotels', 
                    'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"macOS"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                    'X-client-version': '3.44.1',
                    'X-requested-with': 'cdh-application',
            }
            response = requests.get(url=api_url, headers=header)
            if response.status_code == 200:
                roomtype_matrix = response.json()
            else:
                response_data = response.json()
                print_pretty_json_from_memory(response.json())
                ErrorTitle = response_data.get("title")
                st.error(f"ERROR : récuperation de la matrice des type de chambre impossible - mettre à jour les cookies - Description de l'Erreur : {ErrorTitle}")
            #roomtype_matrix = load_data('./roomTypeMatrix.json') # old version of roomtype matrix
            return roomtype_matrix
    except Exception as e:
        print(f"AFD - ERROR : in function get_roomtype_matrix - Error: {e}")
##########################################################################
### AFD Comment - END - Set of Functions to read some data from JW Hub ###
##########################################################################





###################################################################################
### AFD Comment - START - Set of Functions AND COMMAND to setup the environment ###
###################################################################################
### Function to load the CSS file for web page ###
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


### Function to setup global variables ###
def initialization():
    try:
        #global TOKEN; TOKEN = config.TMPToken
        #global COOKIE; COOKIE = config.TMPCookie
        global BASEURL; BASEURL = config.JW_BASE_URL
        global ROOMTYPE_MATRIX

        #global ROOMINGID; ROOMINGID = config.IDCG_HOTEL_ID
        #global CONTRACTID; CONTRACTID = config.IDCG_CONTRACT_2025
        #global COH_ASSIGNMENT_LIST; COH_ASSIGNMENT_LIST = config.IDCG_COH_ASSIGNMENT_LIST_2025
        #global ROOM_TYPE_BLOCK_SIZE_MATRIX; ROOM_TYPE_BLOCK_SIZE_MATRIX = config.IDCG_ROOM_TYPE_BLOCK_SIZE_MATRIX_2025

        #global LISTE_ASSEMBLEES; LISTE_ASSEMBLEES = load_data('./event.json')
        #global EVENT_LIST; EVENT_LIST = ["DREUX1 2025"]
        #global EVENT_LIST; EVENT_LIST = [
        #    "DREUX2 2025", "DREUX3 2025", "DREUX4 2025", "DREUX5 2025", "DREUX6 2025", "DREUX7 2025",
        #    "DREUX8 2025", "DREUX9 2025", "DREUX10 2025", "DREUX11 2025", "DREUX12 2025", "DREUX13 2025"]
    except Exception as e:
        print(f"AFD - ERROR : in function initialization - Error: {e}")  


# Initialisation des variables globale et chargement du fichier CSS ###
st.set_page_config(page_title="JW Rooming", layout="wide")
initialization()
load_css("style.css")


# Initialisation de la variable dans le session state ###
if 'first_event_id' not in st.session_state:
    #st.session_state.first_event_id = None
    first_event_id = '' ### AFD Comment Mettre None si erreur...
    st.session_state["first_event_id"] = first_event_id
if 'hotel_data' not in st.session_state:
    hotel_data = []
    st.session_state["hotel_data"] = hotel_data
if 'events_data' not in st.session_state:
    events_data = []
    st.session_state["events_data"] = events_data
if 'selected_events' not in st.session_state:
    selected_events = []
    st.session_state["selected_events"] = selected_events
if 'room_reservations_by_day' not in st.session_state:
    room_reservations_by_day = {}
    st.session_state["room_reservations_by_day"] = room_reservations_by_day
if 'event_name_list' not in st.session_state:
    event_name_list = []
    st.session_state["event_name_list"] = event_name_list
if 'hotel_cookie' not in st.session_state:
    hotel_cookie = ''
    st.session_state["hotel_cookie"] = hotel_cookie
if 'hotel_token' not in st.session_state:
    hotel_token = ''
    st.session_state["hotel_token"] = hotel_token
#################################################################################
### AFD Comment - END - Set of Functions AND COMMAND to setup the environment ###
#################################################################################




##############################################
### AFD Comment - START - Web page content ###
##############################################
### Web page header ###
st.markdown("""
<div id="header-container">
    <div id="logo-square">JW<br>Hub</div> 
    <div id="title-bar">JW Rooming Tool - for rooming block size assignment</div>
</div>
""", unsafe_allow_html=True)
st.write("Bienvenue dans l'outil JW Rooming Tool !")



### First section : Fill in token and cookie to get event list  ###
st.write("### Récupération de la liste des assemblées")
event_cookie = st.text_input("Fournir le cookie pour la liste des assemblées")
event_token = '' ### st.text_input("Fournir le token pour la liste des assemblées") ### AFD Comment - Le token étant dans le cookie, on devrait pouvoir retirer cette ligne et le test relatif
if st.button("Récupérer les événements"):
    if event_cookie:# and event_token:
        events_data = get_all_events_data(BASEURL, event_token, event_cookie)
        st.session_state["events_data"] = events_data
        event_name_list = []
        for event in events_data:
            event_name_list.append(event.get('name'))
        st.session_state["event_name_list"] = event_name_list
        st.session_state["first_event_id"] = events_data[0].get('eventGuid')
    else:
        st.error("Merci de fournir à la fois le cookie et le token svp.")
st.write("##### ")



### Second section : Fill in token and cookie to get hotel and contract list (from first event (convention)) ###
st.write("### Récupération de la liste des hotels et types de chambre")
hotel_cookie = st.text_input("Fournir le cookie pour la liste des hotels")
hotel_token = st.text_input("Fournir le token pour la liste des hotels") ### AFD Comment - Use Chrome dev tool to get token
if st.button("Récupérer les hotels"):
    hotel_data = get_all_hotels_data(BASEURL, hotel_token, hotel_cookie, st.session_state["first_event_id"]) 
    ### AFD COMMENT - we considere all hotels and contracts have been created in the first event even if it won't be used for this event.
    st.session_state["hotel_data"] = hotel_data
    st.session_state["hotel_cookie"] = hotel_cookie
    st.session_state["hotel_token"] = hotel_token
    print_pretty_json_from_memory(hotel_data)
st.write("##### ")

st.write("### Information pour la création des lots")
hotels = []
hotel_data = st.session_state["hotel_data"]
for hotel in hotel_data:
    hotels.append(hotel.get("hotelName"))
hotels.sort()

room_types = ["Chambre Type 0"] # temporary room type list
#events = []
#for event in st.session_state["events_data"]:
#    events.append(event.get('name'))



### Third section : Select events, hotels and Provide romm block organizations  ###
col1, col2, col3, col4 = st.columns(4)
# Colonne 1 : event multi-selection
with col1:
    #selected_events = st.multiselect("Sélectionner les événements", events)
    selected_events = st.multiselect("Sélectionner les événements", st.session_state["event_name_list"])
    st.session_state['selected_events'] = selected_events

# Colonne 2 : Sélection des types de chambres et du nombre de chambres par jour (Thursday-Sunday)
with col2:
    selected_hotel = ''
    selected_hotel = st.selectbox("Sélectionner un hôtel", hotels)
    st.session_state["selected_hotel"] = selected_hotel
    ROOMTYPE_MATRIX = get_roomtype_matrix(BASEURL, st.session_state["hotel_cookie"], st.session_state["first_event_id"])


# Colonne 3 : Nombre de chambres assignées par l'organisateur (pour chaque jour)
room_types_and_counts = {}
selected_hotel = st.session_state["selected_hotel"]
hotel_data = st.session_state["hotel_data"]
selected_hotel_id = get_value_from_matrix_by_tag(hotel_data, 'hotelName', selected_hotel, 'hotelGuid')
selected_hotel_contract_id = get_value_from_matrix_by_tag(hotel_data, 'hotelName', selected_hotel, 'contractGuid')
selected_hotel_roomtype_list = get_value_from_matrix_by_tag(hotel_data, 'hotelName', selected_hotel, 'roomTypes')
selected_hotel_roomtype_name_list = []
if selected_hotel_roomtype_list:
    for selected_hotel_roomtype in selected_hotel_roomtype_list:
        roomtype_id = selected_hotel_roomtype.get("eventRoomTypeGuid")
        selected_hotel_roomtype_name = get_value_from_matrix_by_tag(ROOMTYPE_MATRIX, 'eventRoomTypeGuid', roomtype_id, 'description')
        selected_hotel_roomtype_name_list.append(selected_hotel_roomtype_name)
    selected_hotel_roomtype_name_list.sort()
    room_types = selected_hotel_roomtype_name_list
with col3:
    st.session_state["room_reservations_by_day"] = {}
    room_reservations_by_day = st.session_state["room_reservations_by_day"]
    st.write("Taille du lot (par type et par jour)")
    for room in room_types:
        st.write(f"**{room}**")
        room_reservations_by_day[room] = {
            'Thursday': st.number_input(f"{room} - Thursday", min_value=0, value=0, step=1, key=f"{room}_jeudi"),
            'Friday': st.number_input(f"{room} - Friday", min_value=0, value=0, step=1, key=f"{room}_vendredi"),
            'Saturday': st.number_input(f"{room} - Saturday", min_value=0, value=0, step=1, key=f"{room}_samedi"),
            'Sunday': st.number_input(f"{room} - Sunday", min_value=0, value=0, step=1, key=f"{room}_dimanche")
        }
    st.session_state["room_reservations_by_day"] = room_reservations_by_day

# Colonne 4 : Nombre de chambres assignées par l'organisateur (pour chaque jour)
organizer_room_assignments = {}
with col4:
    st.write("Chambres assignées par l'organisateur TJ")
    organizer_room_assignments['Thursday'] = st.number_input("Thursday", min_value=0, value=0, step=1, key="jeudi")
    organizer_room_assignments['Friday'] = st.number_input("Friday", min_value=0, value=0, step=1, key="vendredi")
    organizer_room_assignments['Saturday'] = st.number_input("Saturday", min_value=0, value=0, step=1, key="samedi")
    organizer_room_assignments['Sunday'] = st.number_input("Sunday", min_value=0, value=0, step=1, key="dimanche")

# Ajouter la checkbox à la page
display_on_RL = st.checkbox("Rendre visible dans LLHR", value=False)

# Last button : Ajouter un bouton pour générer le fichier JSON
if st.button("Créer les blocs"):
    hotel_name = st.session_state["selected_hotel"]
    room_reservations_by_day = st.session_state["room_reservations_by_day"]
    selected_events = st.session_state["selected_events"]
    events_data = st.session_state["events_data"]
    for event in selected_events:
        event_id = get_value_from_matrix_by_tag(events_data, 'name', event, 'eventGuid')
        event_start_date = get_value_from_matrix_by_tag(events_data, 'name', event, 'startDate')
        #display_on_RL = False
        json_rooming_block = create_json_rooming_block(selected_hotel_id, selected_hotel_contract_id, event_id, event_start_date, room_reservations_by_day, organizer_room_assignments, display_on_RL)
        print(f"INFO - Print json block creation on HOTEL : {hotel_name} - for EVENT {event}")
        print_pretty_json_from_memory(json_rooming_block)
        add_room_block(BASEURL, st.session_state["hotel_token"], st.session_state["hotel_cookie"], json_rooming_block)



# Ajouter une barre de pied de page
st.markdown("""
<div id="footer-bar">
    © 2024 - JW Rooming Tool
</div>
""", unsafe_allow_html=True)