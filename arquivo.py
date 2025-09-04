import pandas as pd
import networkx as nx
import pydesk

colunas = [
    "airline",               # string
    "airline_id",            # int ou \N
    "source_airport",        # string
    "source_airport_id",     # int ou \N
    "destination_airport",   # string
    "destination_airport_id",# int ou \N
    "codeshare",             # string ou vazio
    "stops",                 # int
    "equipment"              # string
]

df = pd.read_csv(
    "arquivos/routes.csv",
    header=None,       # porque não tem cabeçalho
    names=colunas,
    na_values="Null"    # o OpenFlights usa "\N" para valores nulos
)

df = pd.read_csv("arquivos/routes.csv")
grafo = {}

for i, linhas in df.iterrows():
  origem = linhas[2]
  destino = linhas[4]

  if origem not in grafo:
    grafo[origem] = []
  if destino not in grafo:
    grafo[destino] = []

  grafo[origem].append(destino)