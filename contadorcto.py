import streamlit as st
import tempfile
from drive_auth import autenticar_google_drive, baixar_arquivo_drive
from xml.etree import ElementTree as ET
import csv
import io
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Autenticação com Google Drive
def autenticar_google_drive():
    creds = None
    # Carregar credenciais do arquivo JSON
    with open("credentials.json") as source:
        creds_info = json.load(source)
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/drive"])
    
    # Criar serviço Drive API
    service = build("drive", "v3", credentials=creds)
    return service

# Buscar arquivo KML no Google Drive
def baixar_arquivo_drive(service, file_id, nome_saida):
    request = service.files().get_media(fileId=file_id)
    with open(nome_saida, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    return nome_saida


# Função para extrair dados do KML
def extrair_dados_kml(arquivo_kml):
    tree = ET.parse(arquivo_kml)
    root = tree.getroot()
    placemarks = root.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
    dados_placemarks = []

    for placemark in placemarks:
        point = placemark.find('.//{http://www.opengis.net/kml/2.2}Point')
        if point is not None:
            name = placemark.findtext('.//{http://www.opengis.net/kml/2.2}name')
            coordinates = point.findtext('.//{http://www.opengis.net/kml/2.2}coordinates')
            if coordinates:
                parts = coordinates.strip().split(',')
                if len(parts) >= 2:
                    longitude = parts[0]
                    latitude = parts[1]
                    latitude_longitude = f"{latitude},{longitude}"
                    dados_placemarks.append((name, latitude_longitude))

    return dados_placemarks

# Interface Streamlit
st.title("Extrator de Dados KML do Google Drive para CSV")

file_id = st.text_input("https://drive.google.com/file/d/16sPR0qxkCVZm7fEy2hGz0IcHokC1jJvU/view?usp=drive_link")

if st.button("Baixar e Processar"):
    if file_id:
        service = autenticar_google_drive()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as temp_kml:
            arquivo_kml = baixar_arquivo_drive(service, file_id, temp_kml.name)

        dados_placemarks = extrair_dados_kml(arquivo_kml)

        if dados_placemarks:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_csv:
                with open(temp_csv.name, "w", newline="", encoding="utf-8-sig") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Name", "Latitude Longitude"])
                    for linha in dados_placemarks:
                        writer.writerow(linha)

            with open(temp_csv.name, "rb") as file:
                st.download_button(
                    label="Baixar CSV",
                    data=file,
                    file_name="dados_extraidos.csv",
                    mime="text/csv"
                )

            st.success("Arquivo CSV gerado com sucesso!")
        else:
            st.warning("Nenhum placemark válido encontrado no arquivo.")
    else:
        st.error("Por favor, insira um ID de arquivo válido.")

