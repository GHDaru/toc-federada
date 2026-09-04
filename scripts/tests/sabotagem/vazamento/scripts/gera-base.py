#!/usr/bin/env python3
"""Gera a base sintética desta base válida. Nenhuma base real é lida — a origem é o
arquivo sintético versionado aqui dentro (ADR 0001 desta base)."""
import json

ORIGEM = "docs/produto/dados/base-sintetica.json"

def carrega():
    with open(ORIGEM, encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    base = carrega()
    print("nós:", len(base["nos"]), "· sintética:", base["sintetica"])
