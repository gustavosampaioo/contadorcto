import streamlit as st
import tempfile
import json
import csv
import os
from xml.etree import ElementTree as ET
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import re

# Função para autenticação no Google Drive
def autenticar_google_drive():
    try:
        with open("credentials.json") as source:
            creds_info = json.load(source)
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/drive"])
        service = build("drive", "v3", credentials=creds)
        return service
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        return None

# Função para baixar o arquivo KML do Google Drive
def baixar_arquivo_drive(service, file_id):
    try:
        request = service.files().get_media(fileId=file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as temp_kml:
            with open(temp_kml.name, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
        return temp_kml.name
    except Exception as e:
        st.error(f"Erro ao baixar o arquivo do Google Drive: {e}")
        return None

# Função para extrair o ID do link do Google Drive
def extrair_id_google_drive(link):
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
    return match.group(1) if match else None

# Função para extrair dados do KML
def extrair_dados_kml(arquivo_kml):
    try:
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
    except Exception as e:
        st.error(f"Erro ao processar o arquivo KML: {e}")
        return None

# Interface Streamlit
st.title("📍 Extrator de Dados KML do Google Drive para CSV")

link_drive = st.text_input("Cole aqui o link do arquivo KML no Google Drive:")

if st.button("Baixar e Processar"):
    file_id = extrair_id_google_drive(link_drive)

    if not file_id:
        st.error("Link inválido! Certifique-se de copiar o link correto do Google Drive.")
    else:
        st.info("Autenticando no Google Drive...")
        service = autenticar_google_drive()
        
        if service:
            st.info("Baixando arquivo...")
            arquivo_kml = baixar_arquivo_drive(service, file_id)
            
            if arquivo_kml:
                st.success("Arquivo KML baixado com sucesso! Processando...")

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
                            label="📥 Baixar CSV",
                            data=file,
                            file_name="dados_extraidos.csv",
                            mime="text/csv"
                        )

                    st.success("Arquivo CSV gerado com sucesso! 🎉")
                else:
                    st.warning("Nenhum placemark válido encontrado no arquivo.")
