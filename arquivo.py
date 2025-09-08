import streamlit as st
import pandas as pd
import networkx as nx
import pydeck as pdk
import math

st.set_page_config(layout="wide")

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

colunas_rotas = [
    "companhia_aerea","companhia_id","aeroporto_origem","aeroporto_origem_id",
    "aeroporto_destino","aeroporto_destino_id","codeshare",
    "paradas","equipamento"
]
rotas = pd.read_csv("arquivos/routes.csv", header=None, names=colunas_rotas, na_values="\\N")

colunas_aeroportos = [
    "aeroporto_id","nome","cidade","pais","IATA","ICAO",
    "latitude","longitude","altitude","fuso_horario","DST",
    "tz_database","tipo","fonte"
]
aeroportos = pd.read_csv("arquivos/airports.dat", header=None, names=colunas_aeroportos, na_values="\\N")

coordenadas_aeroportos = {
    linha["IATA"]: (linha["latitude"], linha["longitude"])
    for _, linha in aeroportos.iterrows() if pd.notna(linha["IATA"])
}

grafo = nx.DiGraph()
for _, linha in rotas.iterrows():
    origem = linha["aeroporto_origem"]
    destino = linha["aeroporto_destino"]
    if origem in coordenadas_aeroportos and destino in coordenadas_aeroportos:
        lat1, lon1 = coordenadas_aeroportos[origem]
        lat2, lon2 = coordenadas_aeroportos[destino]
        distancia = calcular_distancia(lat1, lon1, lat2, lon2)
        grafo.add_edge(origem, destino, peso=distancia)

def caminho_bfs(grafo, origem, destino):
    try:
        return nx.shortest_path(grafo, origem, destino)
    except nx.NetworkXNoPath:
        return None

def caminho_dfs(grafo, origem, destino):
    visitados = set()
    caminho = []
    def dfs(atual):
        if atual == destino:
            return True
        visitados.add(atual)
        for vizinho in grafo.neighbors(atual):
            if vizinho not in visitados:
                caminho.append(vizinho)
                if dfs(vizinho):
                    return True
                caminho.pop()
        return False
    caminho.append(origem)
    if dfs(origem):
        return caminho
    return None

def caminho_dijkstra(grafo, origem, destino):
    try:
        return nx.dijkstra_path(grafo, origem, destino, weight="peso")
    except nx.NetworkXNoPath:
        return None

st.title("✈️ Busca entre Aeroportos (BFS / DFS / Dijkstra)")

col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    origem = st.text_input("Aeroporto de origem (IATA)", "BVH")
with col2:
    destino = st.text_input("Aeroporto de destino (IATA)", "JFK")
with col3:
    metodo = st.selectbox("Método de busca", ["BFS", "DFS", "Dijkstra"])

caminho = None
if origem and destino:
    if metodo == "BFS":
        caminho = caminho_bfs(grafo, origem, destino)
    elif metodo == "DFS":
        caminho = caminho_dfs(grafo, origem, destino)
    else:
        caminho = caminho_dijkstra(grafo, origem, destino)

if caminho:
    st.success(f"Rota encontrada: {' -> '.join(caminho)}")

    distancia_total = 0
    linhas_rotas = []
    for i in range(len(caminho) - 1):
        a1, a2 = caminho[i], caminho[i+1]
        lat1, lon1 = coordenadas_aeroportos[a1]
        lat2, lon2 = coordenadas_aeroportos[a2]
        d = calcular_distancia(lat1, lon1, lat2, lon2)
        distancia_total += d
        linhas_rotas.append([[lon1, lat1], [lon2, lat2]])

    st.info(f"Distância total: {round(distancia_total, 2)} km")

    camada_rotas = pdk.Layer(
        "PathLayer",
        data=[{"path": r, "name": f"Rota {i}"} for i, r in enumerate(linhas_rotas)],
        get_path="path",
        get_color=[255, 0, 0],
        width_scale=2,
        width_min_pixels=2,
    )
    camada_pontos = pdk.Layer(
        "ScatterplotLayer",
        data=[{"position": [coordenadas_aeroportos[a][1], coordenadas_aeroportos[a][0]], "name": a} for a in caminho],
        get_position="position",
        get_color=[0, 0, 255],
        get_radius=50000,
    )
    visualizacao = pdk.ViewState(
        latitude=coordenadas_aeroportos[caminho[0]][0],
        longitude=coordenadas_aeroportos[caminho[0]][1],
        zoom=2,
        pitch=0
    )

    st.pydeck_chart(
        pdk.Deck(layers=[camada_rotas, camada_pontos], initial_view_state=visualizacao),
        use_container_width=True
    )
else:
    st.info("Digite a origem e destino válidos para visualizar a rota.")
