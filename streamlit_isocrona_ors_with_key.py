
import streamlit as st
from streamlit_folium import st_folium
import folium
import requests

ORS_API_KEY = "5b3ce3597851110001cf62487ff122fc69bc4f59915e04025bee026d"

st.set_page_config(page_title="Isócronas com ORS", layout="wide")
st.title("Gerador de Isócronas com OpenRouteService (ORS)")

minutes = st.slider("Tempo máximo (em minutos)", min_value=5, max_value=60, value=15)
profile = st.selectbox("Modo de transporte", ["driving-car", "foot-walking", "cycling-regular"])

center = [-2.5298, -44.3028]  # São Luís, MA (ajustado pelo mapa exibido)
m = folium.Map(location=center, zoom_start=13)
click_marker = folium.LatLngPopup()
m.add_child(click_marker)

result = st_folium(m, height=600, width=1000)

if result and result.get("last_clicked"):
    lat = result["last_clicked"]["lat"]
    lon = result["last_clicked"]["lng"]
    st.success(f"Coordenadas selecionadas: {lat:.5f}, {lon:.5f}")

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "locations": [[lon, lat]],
        "range": [minutes * 60],
        "range_type": "time",
        "attributes": ["area"],
        "units": "m"
    }

    url = f"https://api.openrouteservice.org/v2/isochrones/{profile}"

    with st.spinner("Consultando ORS e gerando isócronas..."):
        resp = requests.post(url, headers=headers, json=body)
        if resp.status_code == 200:
            data = resp.json()
            st.subheader("Resposta da API (debug):")
            st.json(data)

            folium_map = folium.Map(location=[lat, lon], zoom_start=13)
            folium.Marker([lat, lon], popup="Ponto Inicial").add_to(folium_map)

            for feature in data["features"]:
                geometry_type = feature["geometry"]["type"]
                coords = feature["geometry"]["coordinates"]

                if geometry_type == "Polygon":
                    geojson = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": coords
                        }
                    }
                    folium.GeoJson(geojson, name="Isócrona").add_to(folium_map)

                elif geometry_type == "MultiPolygon":
                    for poly in coords:
                        geojson = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": poly
                            }
                        }
                        folium.GeoJson(geojson, name="Isócrona").add_to(folium_map)

            st.subheader("Isócronas reais via ORS")
            st_folium(folium_map, height=600, width=1000)
        else:
            st.error(f"Erro na API do ORS: {resp.status_code} - {resp.text}")
else:
    st.info("Clique em algum ponto do mapa para gerar isócronas reais.")
