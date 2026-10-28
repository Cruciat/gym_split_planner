"""Generazione dei PDF con WeasyPrint da template Jinja2 (ADR 0008).

Sta allo stesso livello di ``db``: è un adattatore verso una libreria esterna, usato
dai servizi. Riceve solo dati già calcolati, perché WeasyPrint non esegue JavaScript.
"""
